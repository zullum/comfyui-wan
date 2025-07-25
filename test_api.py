#!/usr/bin/env python3
"""
Test script for the Flask API server
Usage: python test_api.py
"""

import requests
import json
import time
import base64

# Configuration
API_URL = "http://localhost:8288"  # Change to your RunPod URL
# For RunPod, use: http://YOUR_POD_ID-8288.proxy.runpod.net

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_generate_video_with_url():
    """Test video generation with image URL"""
    print("\n📷 Testing video generation with image URL...")
    
    payload = {
        "image": "https://picsum.photos/720/1280",  # Random image
        "positive_prompt": "A beautiful landscape with flowing water",
        "negative_prompt": "blurry, low quality, static",
        "width": 720,
        "height": 1280,
        "steps": 3,  # Reduced for faster testing
        "num_frames": 41,  # Reduced for faster testing
        "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"  # Use 720p model
    }
    
    response = requests.post(f"{API_URL}/generate", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["job_id"]
    return None

def test_generate_video_with_base64():
    """Test video generation with base64 image"""
    print("\n🖼️ Testing video generation with base64 image...")
    
    # Create a simple 1x1 pixel PNG as base64 for testing
    tiny_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    base64_image = f"data:image/png;base64,{base64.b64encode(tiny_png).decode()}"
    
    payload = {
        "image": base64_image,
        "positive_prompt": "A colorful abstract animation",
        "width": 720,
        "height": 1280,
        "steps": 3,
        "num_frames": 41
    }
    
    response = requests.post(f"{API_URL}/generate", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json()["job_id"]
    return None

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
    print("🚀 Starting Flask API tests...")
    print(f"API URL: {API_URL}")
    
    # Test health
    if not test_health():
        print("❌ Health check failed. Is the API server running?")
        return
    
    # Test basic info
    response = requests.get(f"{API_URL}/")
    print(f"\nAPI Info: {response.json()}")
    
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