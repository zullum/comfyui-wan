#!/usr/bin/env python3
"""
Flask API Server for ComfyUI Wan Video Generation
Runs on port 8288 and provides REST API for workflow execution
"""

import os
import json
import uuid
import base64
import tempfile
import time
import requests
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
COMFYUI_API_URL = "http://127.0.0.1:8188"
UPLOAD_FOLDER = "/workspace/ComfyUI/input"
OUTPUT_FOLDER = "/workspace/ComfyUI/output"
WORKFLOW_PATH = "/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json"

# In-memory job storage (use Redis in production)
jobs = {}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_workflow():
    """Load the ComfyUI workflow JSON"""
    try:
        with open(WORKFLOW_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Try alternative paths
        alt_paths = [
            "./workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json",
            "/comfyui-wan/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json"
        ]
        for path in alt_paths:
            try:
                with open(path, 'r') as f:
                    logger.info(f"Loaded workflow from: {path}")
                    return json.load(f)
            except FileNotFoundError:
                continue
        raise FileNotFoundError("Workflow file not found in any location")

def update_workflow_params(workflow, params):
    """Update workflow parameters based on input"""
    
    # Default parameters
    defaults = {
        "positive_prompt": "A beautiful woman walking towards the camera",
        "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清",
        "width": 720,
        "height": 1280,
        "num_frames": 81,
        "steps": 5,
        "cfg_scale": 1.0,
        "cfg_img": 8.0,
        "seed": None,
        "lora_strength": 0.7,
        "frame_rate": 16,
        "interpolation_multiplier": 5,
        "final_frame_rate": 60,
        "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"  # Default to 720p I2V model
    }
    
    # Merge with provided params
    for key, default_value in defaults.items():
        params[key] = params.get(key, default_value)
    
    # Update workflow nodes
    for node in workflow.get("nodes", []):
        node_type = node.get("type")
        
        # Update positive prompt
        if node_type == "Text Prompt (JPS)" and node.get("title") != "Negative Prompt":
            if "widgets_values" not in node:
                node["widgets_values"] = []
            node["widgets_values"] = [params["positive_prompt"]]
        
        # Update negative prompt (identified by Chinese characters)
        elif node_type == "Text Prompt (JPS)" and "色调艳丽" in str(node.get("widgets_values", [])):
            node["widgets_values"] = [params["negative_prompt"]]
        
        # Update image input
        elif node_type == "LoadImage" and node.get("title") == "Input Image":
            filename = params.get("image_filename", "input.jpg")
            node["widgets_values"] = [filename, "image"]
        
        # Update video dimensions and length
        elif node_type == "WanVideoImageClipEncode":
            if "widgets_values" not in node:
                node["widgets_values"] = [1280, 720, 81]
            node["widgets_values"][0] = params["height"]  # height
            node["widgets_values"][1] = params["width"]   # width
            node["widgets_values"][2] = params["num_frames"]  # frames
        
        # Update sampling parameters
        elif node_type == "WanVideoSampler":
            if "widgets_values" not in node:
                node["widgets_values"] = [5, 1.0, 8.0, None, "randomize"]
            widgets = node["widgets_values"]
            widgets[0] = params["steps"]      # steps
            widgets[1] = params["cfg_scale"]  # cfg
            widgets[2] = params["cfg_img"]    # cfg_img
            if params["seed"] is not None:
                widgets[3] = params["seed"]   # seed
                widgets[4] = "fixed"          # seed control
        
        # Update LoRA strength
        elif node_type == "WanVideoLoraSelect" and "Self Forcing" in node.get("title", ""):
            if "widgets_values" not in node:
                node["widgets_values"] = ["", 0.7]
            node["widgets_values"][1] = params["lora_strength"]
        
        # Update WanVideoModelLoader to use 720p I2V model by default
        elif node_type == "WanVideoModelLoader":
            if "widgets_values" not in node:
                node["widgets_values"] = ["wan2.1_i2v_720p_14B_bf16.safetensors", "bf16", "fp8_e5m2"]
            # Force 720p I2V model as default
            node["widgets_values"][0] = params.get("model_name", "wan2.1_i2v_720p_14B_bf16.safetensors")
            # Keep existing precision settings or set defaults
            if len(node["widgets_values"]) < 2:
                node["widgets_values"].append("bf16")
            if len(node["widgets_values"]) < 3:
                node["widgets_values"].append("fp8_e5m2")
    
    return workflow

def monitor_job(job_id, prompt_id):
    """Monitor ComfyUI job progress in background thread"""
    jobs[job_id]["status"] = "processing"
    
    try:
        while True:
            time.sleep(2)
            
            # Check ComfyUI history
            response = requests.get(f"{COMFYUI_API_URL}/history/{prompt_id}", timeout=10)
            if response.status_code == 200:
                history = response.json()
                
                if prompt_id in history:
                    execution = history[prompt_id]
                    
                    # Check if completed
                    if "outputs" in execution:
                        # Find output files
                        output_files = []
                        for node_id, node_output in execution["outputs"].items():
                            if "filenames" in node_output:
                                for file_info in node_output["filenames"]:
                                    output_path = os.path.join(
                                        OUTPUT_FOLDER,
                                        file_info.get("subfolder", ""),
                                        file_info["filename"]
                                    )
                                    if os.path.exists(output_path):
                                        output_files.append({
                                            "filename": file_info["filename"],
                                            "path": output_path,
                                            "subfolder": file_info.get("subfolder", "")
                                        })
                        
                        jobs[job_id].update({
                            "status": "completed",
                            "completed_at": datetime.now().isoformat(),
                            "output_files": output_files
                        })
                        return
                    
                    # Check for errors
                    elif "status" in execution and not execution["status"].get("completed", True):
                        error_msg = execution.get("status", {}).get("messages", ["Unknown error"])
                        jobs[job_id].update({
                            "status": "failed",
                            "error": str(error_msg),
                            "completed_at": datetime.now().isoformat()
                        })
                        return
            
            # Timeout after 30 minutes
            if time.time() - jobs[job_id]["created_at_timestamp"] > 1800:
                jobs[job_id].update({
                    "status": "timeout",
                    "error": "Job timed out after 30 minutes",
                    "completed_at": datetime.now().isoformat()
                })
                return
                
    except Exception as e:
        jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        "name": "ComfyUI Wan Video Generation API",
        "version": "1.0.0",
        "endpoints": {
            "POST /generate": "Generate video from image",
            "GET /status/<job_id>": "Get job status",
            "GET /download/<job_id>": "Download result video",
            "GET /jobs": "List all jobs",  
            "GET /health": "Health check"
        },
        "example": {
            "url": "/generate",
            "method": "POST",
            "data": {
                "image": "base64_encoded_image_or_url",
                "positive_prompt": "A beautiful woman walking",
                "width": 720,
                "height": 1280,
                "steps": 5,
                "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"
            }
        },
        "available_models": [
            "wan2.1_i2v_720p_14B_bf16.safetensors",
            "wan2.1_i2v_480p_14B_bf16.safetensors", 
            "wan2.1_t2v_14B_bf16.safetensors",
            "wan2.1_t2v_1.3B_bf16.safetensors"
        ]
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test ComfyUI connection
        response = requests.get(f"{COMFYUI_API_URL}/system_stats", timeout=5)
        comfyui_status = "up" if response.status_code == 200 else "down"
    except:
        comfyui_status = "down"
    
    return jsonify({
        "status": "healthy",
        "comfyui": comfyui_status,
        "jobs_count": len(jobs),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    """Generate video from image and parameters"""
    try:
        # Get JSON data
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        # Validate required fields
        if 'image' not in data:
            return jsonify({"error": "Missing required field: image"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Process image input
        image_filename = None
        if data['image'].startswith('http'):
            # Download from URL
            response = requests.get(data['image'])
            if response.status_code == 200:
                image_filename = f"input_{job_id}.jpg"
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                with open(image_path, 'wb') as f:
                    f.write(response.content)
            else:
                return jsonify({"error": "Failed to download image from URL"}), 400
                
        elif data['image'].startswith('data:image/'):
            # Base64 encoded image
            header, encoded = data['image'].split(',', 1)
            image_data = base64.b64decode(encoded)
            image_filename = f"input_{job_id}.png"
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            with open(image_path, 'wb') as f:
                f.write(image_data)
        else:
            return jsonify({"error": "Image must be URL or base64 encoded"}), 400
        
        # Load and update workflow
        workflow = load_workflow()
        params = data.copy()
        params['image_filename'] = image_filename
        updated_workflow = update_workflow_params(workflow, params)
        
        # Submit to ComfyUI
        comfy_payload = {"prompt": updated_workflow}
        response = requests.post(f"{COMFYUI_API_URL}/prompt", json=comfy_payload, timeout=30)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to submit to ComfyUI", "details": response.text}), 500
        
        prompt_id = response.json().get("prompt_id")
        if not prompt_id:
            return jsonify({"error": "No prompt_id returned from ComfyUI"}), 500
        
        # Create job record
        jobs[job_id] = {
            "job_id": job_id,
            "prompt_id": prompt_id,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "created_at_timestamp": time.time(),
            "parameters": params,
            "image_filename": image_filename
        }
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_job, args=(job_id, prompt_id))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return jsonify({
            "job_id": job_id,
            "prompt_id": prompt_id,
            "status": "queued",
            "message": "Video generation started"
        })
        
    except Exception as e:
        logger.error(f"Error in generate_video: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    return jsonify(job)

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    return jsonify({
        "jobs": list(jobs.values()),
        "total": len(jobs)
    })

@app.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download result video"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    if job["status"] != "completed":
        return jsonify({"error": f"Job not completed. Status: {job['status']}"}), 400
    
    if not job.get("output_files"):
        return jsonify({"error": "No output files found"}), 404
    
    # Return first video file
    output_file = job["output_files"][0]
    if os.path.exists(output_file["path"]):
        return send_file(output_file["path"], as_attachment=True, 
                        download_name=output_file["filename"])
    else:
        return jsonify({"error": "Output file not found on disk"}), 404

if __name__ == '__main__':
    logger.info("🚀 Starting ComfyUI Flask API Server on port 8288...")
    logger.info(f"ComfyUI URL: {COMFYUI_API_URL}")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    
    app.run(host='0.0.0.0', port=8288, debug=False, threaded=True)