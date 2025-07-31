#!/usr/bin/env python3
"""
FastAPI ComfyUI Interface v3
Simple FastAPI server that interfaces directly with ComfyUI WebSocket API
Loads specific workflow and accepts prompt format node updates
"""

import json
import os
import uuid
import websocket
import urllib.request
import urllib.parse
import requests
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComfyUI FastAPI Interface",
    description="Direct ComfyUI WebSocket API interface with workflow support",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
COMFYUI_SERVER = "127.0.0.1:8188"
WORKFLOW_FILE = "/ComfyUI/user/default/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS-API.json"
CLIENT_ID = str(uuid.uuid4())

class WorkflowManager:
    """Manages the ComfyUI workflow loading and processing"""
    
    def __init__(self, workflow_path: str):
        self.workflow_path = workflow_path
        self.base_workflow = self._load_workflow()
    
    def _load_workflow(self) -> Dict:
        """Load the workflow from JSON file"""
        try:
            with open(self.workflow_path, 'r') as f:
                workflow = json.load(f)
            logger.info(f"Loaded workflow from {self.workflow_path}")
            return workflow
        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            return {}
    
    def create_prompt(self, prompt_updates: Dict[str, Any]) -> Dict:
        """Create a ComfyUI prompt by updating the base workflow"""
        # Start with base workflow
        prompt = json.loads(json.dumps(self.base_workflow))
        
        # Apply updates from the prompt_updates
        for node_id, node_data in prompt_updates.items():
            if node_id in prompt:
                # Update inputs if provided
                if "inputs" in node_data:
                    prompt[node_id]["inputs"].update(node_data["inputs"])
                
                # Update class_type if provided (usually not needed)
                if "class_type" in node_data:
                    prompt[node_id]["class_type"] = node_data["class_type"]
            else:
                # Add new node if it doesn't exist
                prompt[node_id] = node_data
        
        return prompt

class ComfyUIClient:
    """Handles ComfyUI WebSocket communication"""
    
    @staticmethod
    def queue_prompt(prompt: Dict) -> Dict:
        """Submit prompt to ComfyUI API"""
        p = {"prompt": prompt, "client_id": CLIENT_ID}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{COMFYUI_SERVER}/prompt", data=data)
        return json.loads(urllib.request.urlopen(req).read())
    
    @staticmethod
    def get_image(filename: str, subfolder: str, folder_type: str) -> bytes:
        """Download image/video from ComfyUI"""
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{COMFYUI_SERVER}/view?{url_values}") as response:
            return response.read()
    
    @staticmethod
    def get_history(prompt_id: str) -> Dict:
        """Get execution history for a prompt"""
        with urllib.request.urlopen(f"http://{COMFYUI_SERVER}/history/{prompt_id}") as response:
            return json.loads(response.read())
    
    @staticmethod
    def get_outputs(prompt_id: str) -> Dict:
        """Get all outputs for a completed job"""
        history = ComfyUIClient.get_history(prompt_id)[prompt_id]
        output_files = {}
        
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'videos' in node_output:
                videos = []
                for video in node_output['videos']:
                    video_data = ComfyUIClient.get_image(
                        video['filename'], 
                        video['subfolder'], 
                        video['type']
                    )
                    videos.append({
                        'filename': video['filename'],
                        'data': video_data
                    })
                output_files[node_id] = {'videos': videos}
            
            elif 'images' in node_output:
                images = []
                for image in node_output['images']:
                    image_data = ComfyUIClient.get_image(
                        image['filename'], 
                        image['subfolder'], 
                        image['type']
                    )
                    images.append({
                        'filename': image['filename'],
                        'data': image_data
                    })
                output_files[node_id] = {'images': images}
        
        return output_files
    
    @staticmethod
    def wait_for_completion(prompt_id: str) -> bool:
        """Wait for job completion using WebSocket"""
        try:
            ws = websocket.WebSocket()
            ws.connect(f"ws://{COMFYUI_SERVER}/ws?clientId={CLIENT_ID}")
            
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executing':
                        data = message['data']
                        if data['node'] is None and data['prompt_id'] == prompt_id:
                            ws.close()
                            return True
                # Continue for binary data (previews)
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            return False

# Initialize workflow manager
workflow_manager = WorkflowManager(WORKFLOW_FILE)

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: Dict[str, Any]
    webhook: Optional[str] = None

class GenerateResponse(BaseModel):
    job_id: str
    prompt_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    prompt_id: str
    status: str
    outputs: Optional[Dict] = None
    error: Optional[str] = None

# Store active jobs
active_jobs = {}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "ComfyUI FastAPI Interface",
        "version": "3.0.0",
        "description": "Direct ComfyUI WebSocket API interface",
        "comfyui_server": COMFYUI_SERVER,
        "workflow_loaded": bool(workflow_manager.base_workflow)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check ComfyUI connectivity
        response = requests.get(f"http://{COMFYUI_SERVER}/system_stats", timeout=5)
        comfyui_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        comfyui_status = "unreachable"
    
    return {
        "status": "healthy",
        "comfyui_status": comfyui_status,
        "workflow_loaded": bool(workflow_manager.base_workflow)
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate video using ComfyUI workflow with prompt updates"""
    
    try:
        # Create the final prompt
        final_prompt = workflow_manager.create_prompt(request.prompt)
        
        # Submit to ComfyUI
        result = ComfyUIClient.queue_prompt(final_prompt)
        prompt_id = result['prompt_id']
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store job info
        active_jobs[job_id] = {
            'prompt_id': prompt_id,
            'status': 'queued',
            'webhook': request.webhook
        }
        
        logger.info(f"Job {job_id} submitted with prompt_id {prompt_id}")
        
        return GenerateResponse(
            job_id=job_id,
            prompt_id=prompt_id,
            status="queued",
            message="Job submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Get job status"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job_info = active_jobs[job_id]
        prompt_id = job_info['prompt_id']
        
        # Check history for completion
        try:
            history = ComfyUIClient.get_history(prompt_id)
            if prompt_id in history:
                job_data = history[prompt_id]
                if 'outputs' in job_data:
                    # Job completed
                    active_jobs[job_id]['status'] = 'completed'
                    return JobStatus(
                        job_id=job_id,
                        prompt_id=prompt_id,
                        status="completed",
                        outputs=job_data['outputs']
                    )
        except:
            pass  # Still running
        
        # Job still running
        return JobStatus(
            job_id=job_id,
            prompt_id=prompt_id,
            status=active_jobs[job_id]['status']
        )
        
    except Exception as e:
        logger.error(f"Error checking job status: {e}")
        active_jobs[job_id]['status'] = 'error'
        return JobStatus(
            job_id=job_id,
            prompt_id=active_jobs[job_id]['prompt_id'],
            status="error",
            error=str(e)
        )

@app.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download job result"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        job_info = active_jobs[job_id]
        prompt_id = job_info['prompt_id']
        
        # Get outputs
        outputs = ComfyUIClient.get_outputs(prompt_id)
        
        if not outputs:
            raise HTTPException(status_code=404, detail="No outputs available")
        
        # Return the first video found
        for node_id, node_outputs in outputs.items():
            if 'videos' in node_outputs and node_outputs['videos']:
                video = node_outputs['videos'][0]
                return {
                    "job_id": job_id,
                    "filename": video['filename'],
                    "download_url": f"http://{COMFYUI_SERVER}/view?filename={video['filename']}&type=output"
                }
        
        raise HTTPException(status_code=404, detail="No video outputs found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading result: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/info")
async def get_workflow_info():
    """Get information about the loaded workflow"""
    if not workflow_manager.base_workflow:
        raise HTTPException(status_code=500, detail="No workflow loaded")
    
    # Extract node information
    nodes_info = {}
    for node_id, node_data in workflow_manager.base_workflow.items():
        nodes_info[node_id] = {
            "class_type": node_data.get("class_type"),
            "inputs": list(node_data.get("inputs", {}).keys()),
            "title": node_data.get("_meta", {}).get("title", "")
        }
    
    return {
        "workflow_file": WORKFLOW_FILE,
        "total_nodes": len(workflow_manager.base_workflow),
        "nodes": nodes_info
    }

@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "total": len(active_jobs),
        "jobs": [
            {
                "job_id": job_id,
                "prompt_id": job_info["prompt_id"],
                "status": job_info["status"]
            }
            for job_id, job_info in active_jobs.items()
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("FASTAPI_PORT", "8189"))
    
    print(f"Starting ComfyUI FastAPI Interface on port {port}")
    print(f"ComfyUI Server: {COMFYUI_SERVER}")
    print(f"Workflow: {WORKFLOW_FILE}")
    print(f"Client ID: {CLIENT_ID}")
    
    uvicorn.run(
        "comfyui_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )