# ComfyUI Wan Video Generation - RunPod Serverless API

This repository provides a RunPod serverless API for generating high-quality videos using the Wan 2.1 video generation model through ComfyUI. The API implements the "Wrapper-SelfForcing-ImageToVideo-60FPS" workflow for converting images to smooth 60fps videos with frame interpolation.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Deployment Guide](#deployment-guide)
- [Environment Variables](#environment-variables)
- [Model Information](#model-information)
- [Troubleshooting](#troubleshooting)

## Features

- **Image-to-Video Generation**: Convert static images to dynamic 60fps videos
- **High Quality Output**: Uses Wan 2.1 14B parameter model for superior quality
- **Frame Interpolation**: RIFE-based interpolation for smooth 60fps output
- **Flexible Parameters**: Customizable prompts, dimensions, frame counts, and more
- **Multiple Output Formats**: S3 upload or base64 encoded responses
- **RunPod Integration**: Optimized for RunPod serverless infrastructure

## Quick Start

### Using Pre-built Docker Image (RunPod Template)

**Image**: `szulic/comfyui-wan:latest-wan`

**Required Ports**:
- 8888 (Jupyter)
- 8188 (ComfyUI) 
- 8288 (Flask API)

**Environment Variables**:
```
SERVE_API_LOCALLY=true
enable_optimizations=true
download_480p_native_models=true
change_preview_method=true
```

### 1. Deploy to RunPod

1. **Create RunPod Pod**:
   - Go to [RunPod Console](https://runpod.io/console/pods)
   - Click "Deploy" on a GPU pod
   - Select "Custom" image: `szulic/comfyui-wan:latest-wan`
   - Configure ports: 8888, 8188, 8288
   - Select GPU: RTX 4090 or better (24GB+ VRAM recommended)

2. **Configure Environment Variables** (optional):
   ```bash
   BUCKET_ENDPOINT_URL=your_s3_endpoint
   BUCKET_ACCESS_KEY_ID=your_access_key
   BUCKET_SECRET_ACCESS_KEY=your_secret_key
   BUCKET_NAME=your_bucket_name
   ```

3. **Deploy and Wait**: The endpoint will build and become ready for use

### 2. Test Your Endpoint

Once deployed, you'll get an endpoint URL like:
```
https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run
```

## API Reference

### Request Format

**Endpoint**: `POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run`

**Headers**:
```json
{
  "Authorization": "Bearer YOUR_RUNPOD_API_KEY",
  "Content-Type": "application/json"
}
```

**Request Body**:
```json
{
  "input": {
    "image": "https://cdn.pixabay.com/photo/2023/07/30/09/12/red-hair-girl-8158373_1280.jpg",
    "positive_prompt": "A beautiful woman walking towards the camera",
    "negative_prompt": "blurry, static, low quality",
    "width": 720,
    "height": 1280,
    "num_frames": 81,
    "steps": 5,
    "cfg_scale": 1.0,
    "cfg_img": 8.0,
    "seed": null,
    "lora_strength": 0.7,
    "frame_rate": 16,
    "interpolation_multiplier": 5,
    "final_frame_rate": 60
  }
}
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|----------|-------------|
| `image` | string | ✅ | - | Input image URL or base64 data |
| `positive_prompt` | string | ❌ | "A beautiful woman walking towards the camera" | Description of desired video content |
| `negative_prompt` | string | ❌ | Anti-quality terms | What to avoid in the video |
| `width` | integer | ❌ | 720 | Video width (must be multiple of 8) |
| `height` | integer | ❌ | 1280 | Video height (must be multiple of 8) |
| `num_frames` | integer | ❌ | 81 | Number of frames to generate |
| `steps` | integer | ❌ | 5 | Denoising steps (3-20) |
| `cfg_scale` | float | ❌ | 1.0 | Text guidance scale |
| `cfg_img` | float | ❌ | 8.0 | Image guidance scale |
| `seed` | integer | ❌ | null | Random seed (null for random) |
| `lora_strength` | float | ❌ | 0.7 | LoRA strength (0.0-1.0) |
| `frame_rate` | integer | ❌ | 16 | Initial frame rate |
| `interpolation_multiplier` | integer | ❌ | 5 | Frame interpolation factor |
| `final_frame_rate` | integer | ❌ | 60 | Final output frame rate |

### Response Format

**Success Response**:
```json
{
  "id": "job_id_here",
  "status": "COMPLETED",
  "output": {
    "video_url": "https://your-bucket.s3.amazonaws.com/video.mp4",
    "metadata": {
      "width": 720,
      "height": 1280,
      "num_frames": 81,
      "frame_rate": 60,
      "duration": 1.35
    }
  }
}
```

**Error Response**:
```json
{
  "id": "job_id_here",
  "status": "FAILED",
  "error": "Error description here"
}
```

## Usage Examples

### Python with requests

```python
import requests
import time
import json

# Configuration
RUNPOD_API_KEY = "your_runpod_api_key"
ENDPOINT_ID = "your_endpoint_id"
API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

# Request payload
payload = {
    "input": {
        "image": "https://example.com/input-image.jpg",
        "positive_prompt": "A serene landscape with gentle water movement",
        "negative_prompt": "blurry, static, low quality, distorted",
        "width": 1280,
        "height": 720,
        "num_frames": 61,
        "steps": 8,
        "cfg_scale": 1.2,
        "final_frame_rate": 30
    }
}

# Submit job (asynchronous)
print("Submitting video generation job...")
response = requests.post(f"{API_URL}/run", json=payload, headers=headers)
response.raise_for_status()

job_data = response.json()
job_id = job_data["id"]
print(f"Job submitted with ID: {job_id}")

# Poll for completion
print("Waiting for completion...")
while True:
    status_response = requests.get(f"{API_URL}/status/{job_id}", headers=headers)
    status_response.raise_for_status()
    
    status_data = status_response.json()
    status = status_data["status"]
    
    print(f"Status: {status}")
    
    if status == "COMPLETED":
        video_url = status_data["output"]["video_url"]
        metadata = status_data["output"]["metadata"]
        
        print(f"✅ Video generated successfully!")
        print(f"📹 Video URL: {video_url}")
        print(f"📊 Duration: {metadata['duration']:.2f} seconds")
        print(f"🎬 Resolution: {metadata['width']}x{metadata['height']}")
        print(f"🎯 Frame Rate: {metadata['frame_rate']} fps")
        break
        
    elif status == "FAILED":
        print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
        break
    
    time.sleep(10)
```

### Python with requests (Synchronous)

```python
import requests

# Configuration
RUNPOD_API_KEY = "your_runpod_api_key"
ENDPOINT_ID = "your_endpoint_id"
API_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAAA...",  # Base64 image
        "positive_prompt": "A butterfly landing on a flower with gentle breeze",
        "width": 768,
        "height": 768,
        "num_frames": 41,
        "steps": 6
    }
}

# Submit synchronous job (waits for completion)
print("Generating video... (this may take several minutes)")
response = requests.post(f"{API_URL}/runsync", json=payload, headers=headers, timeout=600)
response.raise_for_status()

result = response.json()

if result["status"] == "COMPLETED":
    video_url = result["output"]["video_url"]
    print(f"✅ Video ready: {video_url}")
    
    # Save video if base64 encoded
    if video_url.startswith("data:video/"):
        import base64
        video_data = base64.b64decode(video_url.split(',')[1])
        with open("output_video.mp4", "wb") as f:
            f.write(video_data)
        print("📹 Video saved as output_video.mp4")
else:
    print(f"❌ Generation failed: {result.get('error')}")
```

### cURL Examples

**Asynchronous Request**:
```bash
# Submit job
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "https://example.com/image.jpg",
      "positive_prompt": "A peaceful ocean wave",
      "width": 1024,
      "height": 576,
      "num_frames": 61,
      "final_frame_rate": 24
    }
  }'

# Check status (replace JOB_ID with returned ID)
curl -X GET "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/status/JOB_ID" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY"
```

**Synchronous Request**:
```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image": "https://example.com/portrait.jpg",
      "positive_prompt": "A person smiling and waving",
      "negative_prompt": "blurry, distorted, multiple faces",
      "width": 512,
      "height": 768,
      "num_frames": 41,
      "steps": 8,
      "final_frame_rate": 30
    }
  }' \
  --max-time 600
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const RUNPOD_API_KEY = 'your_runpod_api_key';
const ENDPOINT_ID = 'your_endpoint_id';
const API_URL = `https://api.runpod.ai/v2/${ENDPOINT_ID}`;

const headers = {
  'Authorization': `Bearer ${RUNPOD_API_KEY}`,
  'Content-Type': 'application/json'
};

async function generateVideo() {
  try {
    // Submit job
    const payload = {
      input: {
        image: 'https://example.com/input.jpg',
        positive_prompt: 'A cat playing in a garden',
        width: 768,
        height: 768,
        num_frames: 61,
        steps: 6,
        final_frame_rate: 30
      }
    };

    console.log('Submitting video generation job...');
    const response = await axios.post(`${API_URL}/run`, payload, { headers });
    const jobId = response.data.id;
    
    console.log(`Job ID: ${jobId}`);

    // Poll for completion
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
      
      const statusResponse = await axios.get(`${API_URL}/status/${jobId}`, { headers });
      const status = statusResponse.data.status;
      
      console.log(`Status: ${status}`);
      
      if (status === 'COMPLETED') {
        const videoUrl = statusResponse.data.output.video_url;
        const metadata = statusResponse.data.output.metadata;
        
        console.log('✅ Video generated successfully!');
        console.log(`📹 Video URL: ${videoUrl}`);
        console.log(`⏱️ Duration: ${metadata.duration.toFixed(2)} seconds`);
        break;
      } else if (status === 'FAILED') {
        console.error('❌ Job failed:', statusResponse.data.error);
        break;
      }
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

generateVideo();
```

## Deployment Guide

### Option 1: Direct GitHub Deployment (Recommended)

1. **Fork this repository** to your GitHub account

2. **Create RunPod Serverless Endpoint**:
   - Go to [RunPod Console → Serverless](https://runpod.io/console/serverless)
   - Click "New Endpoint"
   - Select "Custom" → "GitHub Repository"
   - Enter your repository URL: `https://github.com/YOUR_USERNAME/comfyui-wan`
   - **GPU Requirements**: 
     - Minimum: RTX 4090 (24GB VRAM)
     - Recommended: A100 (40GB+ VRAM) for best performance
   - **Container Configuration**:
     - Container Disk Size: 50GB+ (for models)
     - Active Workers: 0 (for cost efficiency)
     - Max Workers: 3-5 (based on your needs)
     - Idle Timeout: 30 seconds

3. **Environment Variables** (optional for S3 storage):
   ```bash
   BUCKET_ENDPOINT_URL=your_s3_endpoint
   BUCKET_ACCESS_KEY_ID=your_access_key
   BUCKET_SECRET_ACCESS_KEY=your_secret_key
   BUCKET_NAME=your_bucket_name
   ```

4. **Deploy**: Click "Deploy" and wait for build completion (15-30 minutes)

### Option 2: Docker Hub Deployment

1. **Clone and build**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/comfyui-wan.git
   cd comfyui-wan
   docker build -t your-username/comfyui-wan .
   docker push your-username/comfyui-wan
   ```

2. **Deploy in RunPod**:
   - Select "From Docker Registry"
   - Enter: `your-username/comfyui-wan:latest`
   - Configure GPU and settings as above

### Option 3: Local Development & Testing

1. **Install dependencies**:
   ```bash
   pip install -r builder/requirements.txt
   ```

2. **Set up ComfyUI** (if not using Docker):
   ```bash
   # This would normally be done by the start script
   bash src/start.sh
   ```

3. **Test handler locally**:
   ```bash
   # Set environment variable to skip serverless setup
   export RUNPOD_ENDPOINT_ID=""
   cd src
   python handler.py --rp_serve_api --test_input '{"input": {"image": "https://example.com/test.jpg"}}'
   ```

### Project Structure

The project follows RunPod's recommended structure:

```
comfyui-wan/
├── builder/
│   ├── requirements.txt    # Python dependencies
│   └── setup.sh           # Build-time setup script
├── src/
│   ├── handler.py         # Main serverless handler
│   ├── start.sh           # ComfyUI setup script
│   ├── start_script.sh    # Container startup script
│   └── download.py        # Model download utility
├── workflows/             # ComfyUI workflow files
├── Dockerfile            # Container definition
└── README.md            # Documentation
```

### Deployment Architecture

The deployment process works as follows:

1. **Docker Build Phase**:
   - Base CUDA environment setup with RunPod base image
   - ComfyUI and custom nodes installation
   - RunPod dependencies installation from `builder/requirements.txt`
   - Source files copied from `src/` directory
   - Build verification via `builder/setup.sh`

2. **Container Startup**:
   - `src/handler.py` starts and detects serverless mode
   - Runs setup script to download models and configure ComfyUI
   - Starts ComfyUI server in background
   - Begins accepting RunPod serverless requests

3. **Request Processing**:
   - Handler receives job via RunPod API
   - Validates input and downloads images
   - Executes ComfyUI workflow from `workflows/` directory
   - Returns video URL or base64 data

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BUCKET_ENDPOINT_URL` | ❌ | S3-compatible storage endpoint |
| `BUCKET_ACCESS_KEY_ID` | ❌ | S3 access key |
| `BUCKET_SECRET_ACCESS_KEY` | ❌ | S3 secret key |
| `BUCKET_NAME` | ❌ | S3 bucket name |
| `RUNPOD_DEBUG_LEVEL` | ❌ | Logging level (INFO, DEBUG, etc.) |

**Note**: If S3 variables are not set, videos will be returned as base64 encoded data.

## Model Information

### Wan 2.1 Models Used

- **Main Model**: `wan2.1_i2v_480p_14B_bf16.safetensors` (14B parameters)
- **VAE**: `Wan2_1_VAE_bf16.safetensors`
- **Text Encoder**: `umt5-xxl-enc-bf16.safetensors`
- **CLIP Vision**: `clip_vision_h.safetensors`
- **LoRA**: `Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors`
- **Upscaler**: `4xLSDIR.pth`
- **Frame Interpolation**: RIFE `rife49.pth`

### GPU Requirements

| Model Variant | VRAM Required | Recommended GPU |
|---------------|---------------|----------------|
| 1.3B Model | 8-12GB | RTX 3080, RTX 4070 |
| 14B Model | 20-24GB | RTX 4090, A100 |
| 14B + Interpolation | 24-32GB | RTX 4090, A100, H100 |

## Troubleshooting

### Common Issues

**1. "CUDA out of memory" Error**
- Reduce `num_frames` to 41 or lower
- Use 1.3B model variant instead of 14B
- Reduce image dimensions

**2. "Image must be a URL or base64 encoded data" Error**
- Ensure image URL is accessible
- For base64, include proper data URI prefix: `data:image/jpeg;base64,`

**3. "Width and height must be multiples of 8" Error**
- Adjust dimensions to nearest multiple of 8
- Common valid sizes: 512, 576, 640, 704, 768, 832, 896, 960, 1024, 1280

**4. Slow Generation Times**
- Reduce `steps` to 3-6 for faster generation
- Use smaller frame counts (21-41 frames)
- Disable frame interpolation by setting `final_frame_rate` equal to `frame_rate`

**5. Poor Quality Output**
- Increase `steps` to 8-12
- Adjust `cfg_img` (try 4.0-12.0)
- Use higher resolution inputs
- Improve prompt quality

### Performance Tips

1. **Optimal Settings for Speed**:
   ```json
   {
     "steps": 5,
     "num_frames": 41,
     "width": 512,
     "height": 768,
     "interpolation_multiplier": 3
   }
   ```

2. **Optimal Settings for Quality**:
   ```json
   {
     "steps": 10,
     "num_frames": 81,
     "width": 768,
     "height": 1280,
     "cfg_img": 6.0,
     "interpolation_multiplier": 5
   }
   ```

### Getting Help

- **Repository Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/comfyui-wan/issues)
- **RunPod Support**: [RunPod Discord](https://discord.gg/runpod)
- **ComfyUI Community**: [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- [Wan Video Model](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged) by the Wan team
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) by comfyanonymous
- [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper) by kijai
- [RunPod](https://runpod.io) for serverless infrastructure
- Original workflow by [Hearmeman](https://www.patreon.com/c/HearmemanAI)