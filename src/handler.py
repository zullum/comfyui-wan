#!/usr/bin/env python3
"""
RunPod Serverless Handler for ComfyUI Wan Video Generation
Wrapper-SelfForcing-ImageToVideo-60FPS workflow implementation
"""

import os
import json
import uuid
import base64
import tempfile
import traceback
import subprocess
import time
from typing import Dict, Any, List
from urllib.parse import urlparse
from urllib.request import urlopen, Request
import logging

import runpod
from runpod.serverless.utils import download_files_from_urls, upload_file_to_bucket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ComfyUI API endpoint
COMFYUI_API_URL = "http://127.0.0.1:8188"

def validate_input(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and set default values for input parameters"""
    
    # Required parameters
    if 'image' not in job_input:
        return {"error": "Missing required parameter: 'image'"}
    
    # Set defaults for optional parameters
    defaults = {
        "positive_prompt": "A beautiful woman walking towards the camera",
        "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        "width": 720,
        "height": 1280,
        "num_frames": 81,
        "steps": 5,
        "cfg_scale": 1.0,
        "cfg_img": 8.0,
        "seed": None,  # Will be randomized if None
        "lora_strength": 0.7,
        "frame_rate": 16,
        "interpolation_multiplier": 5,
        "final_frame_rate": 60
    }
    
    # Apply defaults
    for key, default_value in defaults.items():
        job_input[key] = job_input.get(key, default_value)
    
    # Validate dimensions (must be multiples of 8 for VAE)
    if job_input["width"] % 8 != 0 or job_input["height"] % 8 != 0:
        return {"error": "Width and height must be multiples of 8"}
    
    # Validate frame count (must be odd number for proper video generation)
    if job_input["num_frames"] % 2 == 0:
        job_input["num_frames"] += 1
    
    return {"validated_input": job_input}

def download_image(image_input: str, job_id: str) -> str:
    """Download image from URL or decode base64"""
    
    try:
        # Check if it's a URL
        if image_input.startswith(('http://', 'https://')):
            downloaded_files = download_files_from_urls(job_id, [image_input])
            if downloaded_files and downloaded_files[0]:
                return downloaded_files[0]
            else:
                raise ValueError("Failed to download image from URL")
        
        # Check if it's base64 encoded
        elif image_input.startswith('data:image/'):
            # Extract base64 data
            header, encoded = image_input.split(',', 1)
            image_data = base64.b64decode(encoded)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                temp_file.write(image_data)
                return temp_file.name
        
        else:
            raise ValueError("Image must be a URL or base64 encoded data")
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def prepare_workflow(validated_input: Dict[str, Any], image_path: str) -> Dict[str, Any]:
    """Prepare ComfyUI workflow with input parameters"""
    
    # Load the base workflow
    workflow_path = "/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json"
    if not os.path.exists(workflow_path):
        # Fallback to local path if running locally
        workflow_path = "./workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json"
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Update workflow parameters based on input
    for node in workflow["nodes"]:
        node_type = node.get("type")
        
        # Update positive prompt
        if node_type == "Text Prompt (JPS)" and node.get("title") != "Negative Prompt":
            node["widgets_values"] = [validated_input["positive_prompt"]]
        
        # Update negative prompt (identified by Chinese characters in default)
        elif node_type == "Text Prompt (JPS)" and "色调艳丽" in str(node.get("widgets_values", [])):
            node["widgets_values"] = [validated_input["negative_prompt"]]
        
        # Update image input
        elif node_type == "LoadImage" and node.get("title") == "Input Image":
            # Extract filename from path
            filename = os.path.basename(image_path)
            node["widgets_values"] = [filename, "image"]
        
        # Update video dimensions and length
        elif node_type == "WanVideoImageClipEncode":
            node["widgets_values"][0] = validated_input["height"]  # height
            node["widgets_values"][1] = validated_input["width"]   # width
            node["widgets_values"][2] = validated_input["num_frames"]  # frames
        
        # Update sampling parameters
        elif node_type == "WanVideoSampler":
            widgets = node["widgets_values"]
            widgets[0] = validated_input["steps"]      # steps
            widgets[1] = validated_input["cfg_scale"]  # cfg
            widgets[2] = validated_input["cfg_img"]    # cfg_img
            if validated_input["seed"] is not None:
                widgets[3] = validated_input["seed"]   # seed
                widgets[4] = "fixed"                   # seed control
        
        # Update LoRA strength (Self Forcing LoRA)
        elif node_type == "WanVideoLoraSelect" and "Self Forcing" in node.get("title", ""):
            node["widgets_values"][1] = validated_input["lora_strength"]
        
        # Update frame rate for first pass
        elif node_type == "VHS_VideoCombine" and node.get("id") == 80:
            node["widgets_values"]["frame_rate"] = validated_input["frame_rate"]
        
        # Update RIFE interpolation
        elif node_type == "RIFE VFI":
            node["widgets_values"][1] = validated_input["interpolation_multiplier"]
        
        # Update final frame rate
        elif node_type == "VHS_VideoCombine" and node.get("id") == 94:
            node["widgets_values"]["frame_rate"] = validated_input["final_frame_rate"]
    
    return workflow

def execute_comfyui_workflow(workflow: Dict[str, Any]) -> str:
    """Execute workflow on ComfyUI and return output video path"""
    
    import requests
    import time
    
    try:
        # Submit workflow to ComfyUI
        response = requests.post(f"{COMFYUI_API_URL}/prompt", json={"prompt": workflow})
        response.raise_for_status()
        
        prompt_id = response.json()["prompt_id"]
        logger.info(f"Submitted workflow with prompt_id: {prompt_id}")
        
        # Poll for completion
        while True:
            time.sleep(2)
            history_response = requests.get(f"{COMFYUI_API_URL}/history/{prompt_id}")
            history_response.raise_for_status()
            
            history = history_response.json()
            if prompt_id in history:
                execution = history[prompt_id]
                if "outputs" in execution:
                    # Find the final video output
                    for node_id, node_output in execution["outputs"].items():
                        if "filenames" in node_output:
                            filenames = node_output["filenames"]
                            if filenames:
                                video_info = filenames[0]
                                video_path = os.path.join("/workspace/ComfyUI/output", 
                                                        video_info.get("subfolder", ""), 
                                                        video_info["filename"])
                                logger.info(f"Video generated: {video_path}")
                                return video_path
                    
                    # If no video found, check for errors
                    if "status" in execution and execution["status"].get("completed") == False:
                        error_msg = execution.get("status", {}).get("messages", ["Unknown error"])
                        raise RuntimeError(f"ComfyUI execution failed: {error_msg}")
            
            time.sleep(3)
    
    except Exception as e:
        logger.error(f"Error executing ComfyUI workflow: {str(e)}")
        raise

def upload_result(video_path: str) -> str:
    """Upload result video to bucket and return URL"""
    
    try:
        # Check if S3 credentials are available
        bucket_creds = {
            'endpointUrl': os.getenv('BUCKET_ENDPOINT_URL'),
            'accessId': os.getenv('BUCKET_ACCESS_KEY_ID'),
            'accessSecret': os.getenv('BUCKET_SECRET_ACCESS_KEY'),
            'bucketName': os.getenv('BUCKET_NAME', 'runpod-outputs')
        }
        
        if all(bucket_creds.values()):
            # Upload to S3
            filename = os.path.basename(video_path)
            presigned_url = upload_file_to_bucket(filename, video_path, bucket_creds)
            logger.info(f"Video uploaded to S3: {presigned_url}")
            return presigned_url
        else:
            # Return as base64 if no S3 configured
            with open(video_path, 'rb') as video_file:
                video_data = video_file.read()
                video_base64 = base64.b64encode(video_data).decode('utf-8')
                return f"data:video/mp4;base64,{video_base64}"
    
    except Exception as e:
        logger.error(f"Error uploading result: {str(e)}")
        raise

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """Main handler function for RunPod serverless"""
    
    job_id = job.get("id", str(uuid.uuid4()))
    job_input = job.get("input", {})
    
    try:
        logger.info(f"🔥 Processing job {job_id} with input: {job_input}")
        
        # Ensure ComfyUI is ready before processing
        logger.info("🔧 Checking ComfyUI readiness...")
        ensure_comfyui_ready()
        logger.info("✅ ComfyUI ready, proceeding with job")
        
        # Validate input
        validation_result = validate_input(job_input)
        if "error" in validation_result:
            return validation_result
        
        validated_input = validation_result["validated_input"]
        
        # Download/process input image
        image_path = download_image(validated_input["image"], job_id)
        
        # Copy image to ComfyUI input directory
        import shutil
        comfyui_input_dir = "/workspace/ComfyUI/input"
        if not os.path.exists(comfyui_input_dir):
            os.makedirs(comfyui_input_dir)
        
        final_image_path = os.path.join(comfyui_input_dir, os.path.basename(image_path))
        shutil.copy2(image_path, final_image_path)
        
        # Prepare workflow
        workflow = prepare_workflow(validated_input, final_image_path)
        
        # Execute workflow
        video_path = execute_comfyui_workflow(workflow)
        
        # Upload result
        video_url = upload_result(video_path)
        
        # Clean up temporary files
        if image_path.startswith('/tmp'):
            os.unlink(image_path)
        
        return {
            "video_url": video_url,
            "metadata": {
                "width": validated_input["width"],
                "height": validated_input["height"],
                "num_frames": validated_input["num_frames"],
                "frame_rate": validated_input["final_frame_rate"],
                "duration": validated_input["num_frames"] / validated_input["final_frame_rate"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        return {
            "error": f"Failed to process video generation: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ComfyUI setup state tracking
_setup_started = False
_comfyui_ready = False

def setup_comfyui():
    """Setup ComfyUI asynchronously to avoid blocking worker initialization"""
    global _setup_started
    
    if _setup_started:
        return True
        
    import subprocess
    import threading
    
    def run_setup():
        """Run setup in background thread"""
        global _comfyui_ready
        try:
            logger.info("Starting ComfyUI setup in background...")
            
            # Check if ComfyUI is already available (container restart case)
            comfyui_path = "/workspace/ComfyUI"
            if os.path.exists(comfyui_path):
                logger.info("ComfyUI directory found, checking if server is running...")
                try:
                    import requests
                    response = requests.get(f"{COMFYUI_API_URL}/", timeout=3)
                    if response.status_code == 200:
                        logger.info("ComfyUI server already running!")
                        _comfyui_ready = True
                        return
                except:
                    pass
            
            # Run the setup script
            logger.info("Running setup script...")
            process = subprocess.Popen(["/start_script.sh"], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # Wait for completion but don't block main thread
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                logger.info("✅ Setup script completed successfully")
                logger.info("📦 Models and ComfyUI are ready")
                _comfyui_ready = True
            else:
                logger.error(f"❌ Setup script failed with code {process.returncode}")
                if stderr:
                    logger.error(f"STDERR: {stderr[:1000]}...")  # Limit log size
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
    
    # Start setup in background thread
    setup_thread = threading.Thread(target=run_setup, daemon=True)
    setup_thread.start()
    _setup_started = True
    
    logger.info("Setup initiated in background, worker ready to accept jobs")
    return True

def ensure_comfyui_ready():
    """Ensure ComfyUI is ready before processing jobs"""
    global _comfyui_ready
    import requests
    import time
    
    # If we already confirmed it's ready, skip checks
    if _comfyui_ready:
        return True
    
    comfyui_path = "/workspace/ComfyUI"
    max_wait_time = 300  # 5 minutes max wait for setup
    check_interval = 5   # Check every 5 seconds
    
    logger.info("Waiting for ComfyUI to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        # Check if ComfyUI directory exists
        if os.path.exists(comfyui_path):
            logger.info("ComfyUI directory found, checking server...")
            
            # Try to connect to ComfyUI server
            try:
                response = requests.get(f"{COMFYUI_API_URL}/", timeout=3)
                if response.status_code == 200:
                    logger.info("ComfyUI server is ready!")
                    _comfyui_ready = True
                    return True
            except requests.exceptions.RequestException:
                # Server not ready yet, try to start it
                logger.info("ComfyUI server not responding, attempting to start...")
                try:
                    subprocess.Popen([
                        "python3", f"{comfyui_path}/main.py", 
                        "--listen", "--use-sage-attention"
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Give it time to start
                    time.sleep(10)
                    continue
                except Exception as e:
                    logger.warning(f"Failed to start ComfyUI: {str(e)}")
        
        logger.info(f"ComfyUI not ready yet, waiting... ({int(time.time() - start_time)}s elapsed)")
        time.sleep(check_interval)
    
    # If we get here, setup is taking too long - but don't fail completely
    logger.warning("ComfyUI setup is taking longer than expected, but will continue processing")
    return True

# Start the serverless handler
if __name__ == "__main__":
    # Check if we should run setup
    if os.getenv("RUNPOD_ENDPOINT_ID"):
        # We're in serverless mode, start setup in background
        logger.info("Starting in RunPod serverless mode")
        setup_comfyui()  # This now runs in background
    else:
        logger.info("Starting in local/development mode")
    
    # Start the serverless handler immediately - setup runs in background
    logger.info("🚀 Starting RunPod serverless handler...")
    
    # Add a simple health check
    def health_check():
        return {"status": "ready", "timestamp": time.time()}
    
    runpod.serverless.start({
        "handler": handler,
        "health": health_check
    })