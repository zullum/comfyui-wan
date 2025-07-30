#!/usr/bin/env python3
"""
Test script for ComfyUI Workflow Wrapper Service

This script demonstrates how to use the wrapper service to:
1. Load workflows dynamically
2. Update parameters with simple payloads
3. Generate videos
4. Track job status
5. Download results
"""

import requests
import time
import json
from typing import Dict, Any

class WorkflowWrapperClient:
    """Client for interacting with the ComfyUI Workflow Wrapper"""
    
    def __init__(self, wrapper_url: str = "http://localhost:8289"):
        self.wrapper_url = wrapper_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the wrapper service is healthy"""
        response = self.session.get(f"{self.wrapper_url}/health")
        response.raise_for_status()
        return response.json()
    
    def list_workflows(self) -> Dict[str, Any]:
        """List available workflows"""
        response = self.session.get(f"{self.wrapper_url}/workflows")
        response.raise_for_status()
        return response.json()
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get information about a specific workflow"""
        response = self.session.get(f"{self.wrapper_url}/workflows/{workflow_name}")
        response.raise_for_status()
        return response.json()
    
    def generate_video(self, **kwargs) -> Dict[str, Any]:
        """Generate video with workflow parameters"""
        response = self.session.post(f"{self.wrapper_url}/generate", json=kwargs)
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job"""
        response = self.session.get(f"{self.wrapper_url}/status/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def get_download_urls(self, job_id: str) -> Dict[str, Any]:
        """Get download URLs for completed job"""
        response = self.session.get(f"{self.wrapper_url}/download/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
        """Wait for a job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            print(f"Job {job_id} status: {status['status']}")
            
            if status['status'] == 'completed':
                return status
            elif status['status'] == 'failed':
                raise Exception(f"Job failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

def test_basic_workflow():
    """Test basic workflow functionality"""
    print("=== Testing Basic Workflow Functionality ===")
    
    client = WorkflowWrapperClient()
    
    # Health check
    print("1. Health check...")
    health = client.health_check()
    print(f"   Service status: {health['status']}")
    print(f"   Workflows loaded: {health['workflows_loaded']}")
    print(f"   ComfyUI API status: {health['comfyui_api_status']}")
    
    # List workflows
    print("\n2. Listing workflows...")
    workflows = client.list_workflows()
    print(f"   Available workflows: {workflows['workflows']}")
    
    if not workflows['workflows']:
        print("   No workflows available - make sure workflow files are in the workflows/ directory")
        return
    
    # Get workflow info
    workflow_name = workflows['workflows'][0]  # Use first available workflow
    print(f"\n3. Getting info for workflow: {workflow_name}")
    info = client.get_workflow_info(workflow_name)
    print(f"   Nodes: {info['nodes']}")
    print(f"   Key nodes: {list(info['key_nodes'].keys())}")
    
    return workflow_name, client

def test_i2v_generation():
    """Test Image-to-Video generation"""
    print("\n=== Testing Image-to-Video Generation ===")
    
    workflow_name, client = test_basic_workflow()
    
    if "SelfForcing-ImageToVideo" not in workflow_name:
        print(f"Skipping I2V test - workflow '{workflow_name}' is not I2V")
        return
    
    # Submit I2V job
    print("\n4. Submitting I2V generation job...")
    job_request = {
        "workflow_name": workflow_name,
        "job_id": f"test-i2v-{int(time.time())}",
        "image": "https://example.com/test-image.jpg",  # Replace with actual image URL
        "positive_prompt": "A beautiful woman walking towards the camera, cinematic lighting",
        "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清",
        "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors",
        "steps": 5,
        "cfg": 1.0,
        "cfg_img": 8.0,
        "seed": -1
    }
    
    result = client.generate_video(**job_request)
    job_id = result['job_id']
    
    print(f"   Job submitted: {job_id}")
    print(f"   Status: {result['status']}")
    print(f"   Prompt ID: {result.get('prompt_id', 'N/A')}")
    
    return job_id, client

def test_job_tracking():
    """Test job status tracking"""
    print("\n=== Testing Job Status Tracking ===")
    
    try:
        job_id, client = test_i2v_generation()
    except Exception as e:
        print(f"Could not start I2V generation: {e}")
        return
    
    # Track job status
    print(f"\n5. Tracking job status for {job_id}...")
    
    try:
        # Wait for completion (with shorter timeout for testing)
        final_status = client.wait_for_completion(job_id, timeout=60, poll_interval=10)
        print(f"   Job completed: {final_status['status']}")
        
        # Get download URLs
        print("\n6. Getting download URLs...")
        downloads = client.get_download_urls(job_id)
        print(f"   Available downloads: {len(downloads['downloads'])}")
        
        for download in downloads['downloads']:
            print(f"   - {download['filename']}: {download['url']}")
    
    except TimeoutError:
        print("   Job did not complete within timeout (this is normal for testing)")
    except Exception as e:
        print(f"   Error during job tracking: {e}")

def test_simple_payload():
    """Test with minimal payload"""
    print("\n=== Testing Simple Payload ===")
    
    client = WorkflowWrapperClient()
    
    try:
        # Simple request with just the essentials
        simple_request = {
            "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
            "image": "https://picsum.photos/720/1280",  # Random image for testing
            "positive_prompt": "A serene landscape with flowing water"
        }
        
        print("7. Submitting simple request...")
        result = client.generate_video(**simple_request)
        
        print(f"   Job ID: {result['job_id']}")
        print(f"   Status: {result['status']}")
        
        # Check initial status
        status = client.get_job_status(result['job_id'])
        print(f"   Initial status: {status['status']}")
        
    except Exception as e:
        print(f"   Error with simple payload: {e}")

def print_usage_examples():
    """Print usage examples"""
    print("\n=== Usage Examples ===")
    
    print("""
# Basic I2V Generation
curl -X POST http://localhost:8289/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
    "image": "https://example.com/image.jpg",
    "positive_prompt": "A beautiful scene",
    "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清"
  }'

# Advanced I2V with all parameters
curl -X POST http://localhost:8289/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
    "job_id": "my-custom-job-id",
    "image": "https://example.com/image.jpg",
    "positive_prompt": "A woman walking towards camera",
    "negative_prompt": "blurry, static, overexposed",
    "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors",
    "steps": 5,
    "cfg": 1.0,
    "cfg_img": 8.0,
    "seed": 42,
    "webhook": "https://your-webhook.com/notify"
  }'

# Check job status
curl http://localhost:8289/status/YOUR_JOB_ID

# Get download URLs
curl http://localhost:8289/download/YOUR_JOB_ID

# List workflows
curl http://localhost:8289/workflows

# Health check
curl http://localhost:8289/health
""")

if __name__ == "__main__":
    print("ComfyUI Workflow Wrapper Test Script")
    print("====================================")
    
    try:
        # Run tests
        test_basic_workflow()
        test_simple_payload()
        
        # Print usage examples
        print_usage_examples()
        
        print("\n=== Test Complete ===")
        print("To run the wrapper service:")
        print("cd src && python workflow_wrapper.py")
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to wrapper service")
        print("Make sure the wrapper service is running on http://localhost:8289")
        print("\nTo start the service:")
        print("cd src && python workflow_wrapper.py")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()