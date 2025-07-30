#!/usr/bin/env python3
"""
ComfyUI Workflow Wrapper Service v2

A precise wrapper service that loads ComfyUI workflows and accepts node-specific updates.
This approach lets you specify exactly which node IDs to update, keeping everything else identical.

Features:
- Load workflows from JSON files exactly as they are
- Accept node_updates payload to modify specific node IDs
- Convert to ComfyUI API format preserving all connections
- Submit complete workflows to ComfyUI API
- Track job status and results
"""

import json
import os
import uuid
import time
import requests
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ComfyUI Workflow Wrapper v2",
    description="Precise workflow loading with node-specific updates for ComfyUI",
    version="2.0.0"
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
COMFYUI_API_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8288")
WORKFLOWS_DIR = Path("workflows")

class WorkflowLoader:
    """Handles loading and caching of ComfyUI workflow files"""
    
    def __init__(self, workflows_dir: Path):
        self.workflows_dir = workflows_dir
        self.workflows_cache = {}
        self.load_workflows()
    
    def load_workflows(self):
        """Load all workflow files from the workflows directory"""
        logger.info(f"Loading workflows from {self.workflows_dir}")
        
        if not self.workflows_dir.exists():
            logger.error(f"Workflows directory not found: {self.workflows_dir}")
            return
        
        for workflow_file in self.workflows_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    workflow_data = json.load(f)
                
                workflow_name = workflow_file.stem
                self.workflows_cache[workflow_name] = workflow_data
                logger.info(f"Loaded workflow: {workflow_name}")
                
            except Exception as e:
                logger.error(f"Error loading workflow {workflow_file}: {e}")
    
    def get_workflow(self, name: str) -> Optional[Dict]:
        """Get a workflow by name"""
        return self.workflows_cache.get(name)
    
    def list_workflows(self) -> List[str]:
        """List available workflow names"""
        return list(self.workflows_cache.keys())

class WorkflowProcessor:
    """Processes workflows with precise node updates"""
    
    def __init__(self, workflow_loader: WorkflowLoader):
        self.workflow_loader = workflow_loader
    
    def process_workflow_request(self, workflow_name: str, node_updates: Dict[str, Any], job_id: Optional[str] = None) -> Dict:
        """Process a workflow request with precise node updates"""
        
        # Get the workflow
        workflow = self.workflow_loader.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Create a deep copy to avoid modifying the original
        workflow_copy = json.loads(json.dumps(workflow))
        
        # Apply node updates
        if node_updates:
            self._apply_node_updates(workflow_copy, node_updates)
        
        # Convert to ComfyUI API format
        api_payload = self._convert_to_api_format(workflow_copy, job_id)
        
        return api_payload
    
    def _apply_node_updates(self, workflow: Dict, node_updates: Dict[str, Any]):
        """Apply updates to specific nodes in the workflow"""
        
        # Create a lookup map for faster node access
        node_map = {}
        for node in workflow.get('nodes', []):
            node_map[str(node['id'])] = node
        
        # Apply updates to each specified node
        for node_id_str, updates in node_updates.items():
            if node_id_str not in node_map:
                logger.warning(f"Node ID {node_id_str} not found in workflow")
                continue
            
            node = node_map[node_id_str]
            
            # Update widgets_values if provided
            if 'widgets_values' in updates:
                node['widgets_values'] = updates['widgets_values']
                logger.info(f"Updated node {node_id_str} widgets_values: {updates['widgets_values']}")
            
            # Update other node properties if provided
            for key, value in updates.items():
                if key != 'widgets_values':
                    node[key] = value
                    logger.info(f"Updated node {node_id_str} {key}: {value}")
    
    def _convert_to_api_format(self, workflow: Dict, job_id: Optional[str] = None) -> Dict:
        """Convert workflow to ComfyUI API format preserving all structure"""
        
        # Generate unique request ID
        if not job_id:
            job_id = str(uuid.uuid4())
        
        # Build the prompt object with numbered nodes
        prompt = {}
        
        for node in workflow.get('nodes', []):
            node_id = str(node['id'])
            node_type = node.get('type')
            
            # Skip certain node types that aren't needed for API execution
            if node_type in ['Note', 'Reroute']:
                continue
            
            # Build node inputs from the workflow structure
            inputs = self._build_node_inputs(node, workflow)
            
            prompt[node_id] = {
                "inputs": inputs,
                "class_type": node_type
            }
        
        # Build the complete API payload
        api_payload = {
            "id": job_id,
            "prompt": prompt
        }
        
        return api_payload
    
    def _build_node_inputs(self, node: Dict, workflow: Dict) -> Dict:
        """Build inputs for a node based on its widget values and connections"""
        inputs = {}
        
        # Add widget values as direct inputs based on node type
        widget_values = node.get('widgets_values', [])
        node_type = node.get('type')
        
        # Map widget values to input names based on node type
        if node_type == 'LoadImage' and widget_values:
            inputs['image'] = widget_values[0]
            if len(widget_values) > 1:
                inputs['upload'] = widget_values[1]
        
        elif node_type == 'Text Prompt (JPS)' and widget_values:
            inputs['text'] = widget_values[0]
        
        elif node_type == 'WanVideoModelLoader' and widget_values:
            if len(widget_values) >= 1:
                inputs['model_name'] = widget_values[0]
            if len(widget_values) >= 2:
                inputs['precision'] = widget_values[1]
            if len(widget_values) >= 3:
                inputs['dtype'] = widget_values[2]
            if len(widget_values) >= 4:
                inputs['device'] = widget_values[3]
            if len(widget_values) >= 5:
                inputs['attention_mode'] = widget_values[4]
        
        elif node_type == 'WanVideoSampler' and widget_values:
            input_names = ['steps', 'cfg', 'cfg_img', 'seed', 'seed_control', 'denoise', 'sampler_name', 'sampler_idx', 'scheduler_idx', 'custom_sigmas', 'scheduler']
            for i, input_name in enumerate(input_names):
                if i < len(widget_values):
                    inputs[input_name] = widget_values[i]
        
        elif node_type == 'WanVideoTextEncode' and widget_values:
            if len(widget_values) >= 1:
                inputs['positive_prompt'] = widget_values[0]
            if len(widget_values) >= 2:
                inputs['negative_prompt'] = widget_values[1]
            if len(widget_values) >= 3:
                inputs['enable_text_encoder_offload'] = widget_values[2]
        
        elif node_type == 'WanVideoImageClipEncode' and widget_values:
            input_names = ['width', 'height', 'num_frames', 'enable_tiling', 'tile_overlap_factor', 'tile_frames_factor', 'tile_batch_factor', 'enable_vae_offload']
            for i, input_name in enumerate(input_names):
                if i < len(widget_values):
                    inputs[input_name] = widget_values[i]
        
        # Handle other node types by using generic widget mapping
        elif widget_values and node_type not in ['LoadImage', 'Text Prompt (JPS)', 'WanVideoModelLoader', 'WanVideoSampler', 'WanVideoTextEncode', 'WanVideoImageClipEncode']:
            # For unknown node types, just pass widget_values as numbered inputs
            for i, value in enumerate(widget_values):
                inputs[f'input_{i}'] = value
        
        # Add connections from other nodes based on the workflow's links
        node_inputs = node.get('inputs', [])
        for input_def in node_inputs:
            input_name = input_def.get('name', '')
            if 'link' in input_def and input_def['link'] is not None:
                # Find the source node for this link
                source_info = self._find_source_for_link(workflow, input_def['link'])
                if source_info:
                    source_node_id, output_slot = source_info
                    inputs[input_name] = [str(source_node_id), output_slot]
        
        return inputs
    
    def _find_source_for_link(self, workflow: Dict, link_id: int) -> Optional[tuple]:
        """Find the source node and output slot for a given link ID"""
        for node in workflow.get('nodes', []):
            for output_idx, output in enumerate(node.get('outputs', [])):
                if 'links' in output and link_id in output['links']:
                    return (node['id'], output_idx)
        return None

    def get_workflow_node_info(self, workflow_name: str) -> Dict:
        """Get detailed information about nodes in a workflow"""
        workflow = self.workflow_loader.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        node_info = {}
        for node in workflow.get('nodes', []):
            node_id = str(node['id'])
            node_type = node.get('type')
            
            # Skip utility nodes
            if node_type in ['Note', 'Reroute']:
                continue
            
            node_info[node_id] = {
                'type': node_type,
                'title': node.get('title', ''),
                'widgets_values': node.get('widgets_values', []),
                'inputs': [inp.get('name', '') for inp in node.get('inputs', [])],
                'outputs': [out.get('name', '') for out in node.get('outputs', [])]
            }
        
        return node_info

# Initialize components
workflow_loader = WorkflowLoader(WORKFLOWS_DIR)
workflow_processor = WorkflowProcessor(workflow_loader)

# Pydantic models for request/response
class NodeUpdate(BaseModel):
    widgets_values: Optional[List[Any]] = None

class WorkflowRequest(BaseModel):
    workflow_name: str
    job_id: Optional[str] = None
    node_updates: Optional[Dict[str, NodeUpdate]] = None
    webhook: Optional[str] = None
    convert_output: Optional[Dict] = None

class WorkflowResponse(BaseModel):
    job_id: str
    status: str
    prompt_id: Optional[str] = None
    message: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[Dict] = None
    outputs: Optional[Dict] = None
    error: Optional[str] = None

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "ComfyUI Workflow Wrapper v2",
        "version": "2.0.0",
        "description": "Precise node-based workflow updates",
        "available_workflows": workflow_loader.list_workflows(),
        "comfyui_api": COMFYUI_API_URL
    }

@app.get("/workflows")
async def list_workflows():
    """List available workflows"""
    return {
        "workflows": workflow_loader.list_workflows(),
        "count": len(workflow_loader.list_workflows())
    }

@app.get("/workflows/{workflow_name}")
async def get_workflow_info(workflow_name: str):
    """Get detailed information about a specific workflow including all node IDs"""
    try:
        node_info = workflow_processor.get_workflow_node_info(workflow_name)
        
        return {
            "workflow_name": workflow_name,
            "total_nodes": len(node_info),
            "updatable_nodes": node_info
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/generate", response_model=WorkflowResponse)
async def generate_video(request: WorkflowRequest):
    """Generate video using a workflow with precise node updates"""
    
    try:
        # Convert node updates to the expected format
        node_updates = {}
        if request.node_updates:
            for node_id, update in request.node_updates.items():
                node_updates[node_id] = update.dict(exclude_none=True)
        
        # Process the workflow request
        api_payload = workflow_processor.process_workflow_request(
            request.workflow_name, 
            node_updates,
            request.job_id
        )
        
        # Add optional parameters
        if request.webhook:
            api_payload['webhook'] = request.webhook
        
        if request.convert_output:
            api_payload['convert_output'] = request.convert_output
        
        # Submit to ComfyUI API
        response = requests.post(
            f"{COMFYUI_API_URL}/prompt",
            json=api_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ComfyUI API error: {response.text}"
            )
        
        result = response.json()
        
        return WorkflowResponse(
            job_id=api_payload["id"],
            status="submitted",
            prompt_id=result.get("prompt_id"),
            message="Workflow submitted successfully"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing workflow request: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a job"""
    
    try:
        # Query ComfyUI API for job status
        response = requests.get(f"{COMFYUI_API_URL}/history/{job_id}")
        
        if response.status_code == 404:
            return JobStatus(job_id=job_id, status="not_found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"ComfyUI API error: {response.text}"
            )
        
        history = response.json()
        
        if job_id not in history:
            return JobStatus(job_id=job_id, status="not_found")
        
        job_data = history[job_id]
        
        # Determine status
        status = "running"
        if "outputs" in job_data:
            status = "completed"
        elif "status" in job_data and job_data["status"].get("completed", False):
            status = "completed"
        
        return JobStatus(
            job_id=job_id,
            status=status,
            progress=job_data.get("status"),
            outputs=job_data.get("outputs"),
            error=job_data.get("error")
        )
        
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/download/{job_id}")
async def download_result(job_id: str):
    """Get download URLs for job results"""
    
    try:
        # Get job status first
        status_response = await get_job_status(job_id)
        
        if status_response.status != "completed":
            raise HTTPException(status_code=400, detail="Job not completed")
        
        if not status_response.outputs:
            raise HTTPException(status_code=404, detail="No outputs available")
        
        # Extract download URLs
        download_urls = []
        for node_id, node_outputs in status_response.outputs.items():
            if "videos" in node_outputs:
                for video in node_outputs["videos"]:
                    filename = video.get("filename")
                    if filename:
                        download_url = f"{COMFYUI_API_URL}/view?filename={filename}&type=output"
                        download_urls.append({
                            "filename": filename,
                            "url": download_url,
                            "node_id": node_id
                        })
        
        return {
            "job_id": job_id,
            "downloads": download_urls
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download URLs: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if ComfyUI API is accessible
        response = requests.get(f"{COMFYUI_API_URL}/health", timeout=5)
        comfyui_status = "healthy" if response.status_code == 200 else "unhealthy"
    except:
        comfyui_status = "unreachable"
    
    return {
        "status": "healthy",
        "workflows_loaded": len(workflow_loader.list_workflows()),
        "comfyui_api_status": comfyui_status,
        "comfyui_url": COMFYUI_API_URL
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("WRAPPER_PORT", "8289"))
    
    print(f"Starting ComfyUI Workflow Wrapper v2 on port {port}")
    print(f"ComfyUI API URL: {COMFYUI_API_URL}")
    print(f"Available workflows: {workflow_loader.list_workflows()}")
    
    uvicorn.run(
        "workflow_wrapper:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )