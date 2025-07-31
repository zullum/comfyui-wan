#!/usr/bin/env python3
"""
Test script for the FastAPI ComfyUI Interface
Usage: python test_api.py
"""

import requests
import json
import time
import base64

# Configuration
API_URL = "http://localhost:8189"  # Change to your RunPod URL
# For RunPod, use: http://YOUR_POD_ID-8189.proxy.runpod.net

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_generate_video_with_url():
    """Test video generation with ComfyUI prompt format"""
    print("\n📷 Testing video generation with ComfyUI prompt format...")
    
    payload = {
        "prompt": {
            "218": {
                "inputs": {
                    "image": "https://picsum.photos/720/1280"
                },
                "class_type": "LoadImage"
            },
            "265": {
                "inputs": {
                    "text": "A beautiful landscape with flowing water"
                },
                "class_type": "Text Prompt (JPS)"
            },
            "266": {
                "inputs": {
                    "text": "blurry, low quality, static"
                },
                "class_type": "Text Prompt (JPS)"
            },
            "215": {
                "inputs": {
                    "generation_width": 720,
                    "generation_height": 1280,
                    "num_frames": 41
                }
            },
            "205": {
                "inputs": {
                    "steps": 3,
                    "seed": 12345
                }
            }
        }
    }
    
    response = requests.post(f"{API_URL}/generate", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["job_id"]
    return None

def test_workflow_info():
    """Test workflow info endpoint"""
    print("\n🔍 Testing workflow info...")
    
    response = requests.get(f"{API_URL}/workflow/info")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Workflow file: {data['workflow_file']}")
        print(f"Total nodes: {data['total_nodes']}")
        print("Key nodes:")
        for node_id, info in list(data['nodes'].items())[:5]:
            print(f"  - {node_id}: {info['class_type']} ({info.get('title', '')})")
    return response.status_code == 200

def monitor_job(job_id):
    """Monitor job progress"""
    print(f"\n⏳ Monitoring job {job_id}...")
    
    while True:
        response = requests.get(f"{API_URL}/status/{job_id}")
        if response.status_code == 200:
            job_data = response.json()
            status = job_data["status"]
            print(f"Status: {status}")
            
            if status == "completed":
                print("✅ Job completed!")
                print(f"Output files: {job_data.get('output_files', [])}")
                return True
            elif status == "failed":
                print(f"❌ Job failed: {job_data.get('error', 'Unknown error')}")
                return False
            elif status in ["timeout"]:
                print(f"⏰ Job {status}")
                return False
        else:
            print(f"Error checking status: {response.status_code}")
            return False
        
        time.sleep(5)

def test_download(job_id):
    """Test downloading result"""
    print(f"\n📥 Testing download for job {job_id}...")
    
    response = requests.get(f"{API_URL}/download/{job_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        filename = f"result_{job_id}.mp4"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {filename}")
        return True
    else:
        print(f"❌ Download failed: {response.text}")
        return False

def test_list_jobs():
    """Test listing all jobs"""
    print("\n📋 Testing job list...")
    
    response = requests.get(f"{API_URL}/jobs")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total jobs: {data['total']}")
        for job in data['jobs'][-3:]:  # Show last 3 jobs
            print(f"  - {job['job_id']}: {job['status']}")

def main():
    """Run all tests"""
    print("🚀 Starting FastAPI ComfyUI Interface tests...")
    print(f"API URL: {API_URL}")
    
    # Test health
    if not test_health():
        print("❌ Health check failed. Is the API server running?")
        return
    
    # Test basic info
    response = requests.get(f"{API_URL}/")
    print(f"\nAPI Info: {response.json()}")
    
    # Test workflow info
    test_workflow_info()
    
    # Test video generation
    job_id = test_generate_video_with_url()
    if job_id:
        # Monitor progress (this will take several minutes)
        if monitor_job(job_id):
            # Try to download
            test_download(job_id)
    
    # List all jobs
    test_list_jobs()
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    main()