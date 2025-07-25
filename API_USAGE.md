# ComfyUI Wan Video Generation API

Simple Flask API server running on port 8288 for ComfyUI workflow automation.

## Endpoints

### `GET /` - API Documentation
Returns API information and usage examples.

### `GET /health` - Health Check
Check if the API and ComfyUI are running.

```bash
curl http://YOUR_POD_ID-8288.proxy.runpod.net/health
```

### `POST /generate` - Generate Video
Generate video from image using the Wan workflow.

**Request Body:**
```json
{
  "image": "https://example.com/image.jpg",  // URL or base64
  "positive_prompt": "A beautiful woman walking towards the camera",
  "negative_prompt": "blurry, low quality, static",
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
  "final_frame_rate": 60,
  "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"  // Model selection
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "prompt_id": "comfyui_prompt_id",
  "status": "queued",
  "message": "Video generation started"
}
```

### `GET /status/<job_id>` - Check Job Status
Check the status of a video generation job.

```bash
curl http://YOUR_POD_ID-8288.proxy.runpod.net/status/JOB_ID
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",  // queued, processing, completed, failed, timeout
  "created_at": "2025-01-24T10:30:00",
  "output_files": [
    {
      "filename": "output_video.mp4",
      "path": "/workspace/ComfyUI/output/output_video.mp4"
    }
  ]
}
```

### `GET /download/<job_id>` - Download Result
Download the generated video file.

```bash
curl -o result.mp4 http://YOUR_POD_ID-8288.proxy.runpod.net/download/JOB_ID
```

### `GET /jobs` - List All Jobs
List all jobs and their statuses.

## Usage Examples

### 1. Basic cURL Example
```bash
# Generate video from URL
curl -X POST http://YOUR_POD_ID-8288.proxy.runpod.net/generate \
  -H "Content-Type: application/json" \
  -d '{
    "image": "https://picsum.photos/720/1280",
    "positive_prompt": "A person walking in a beautiful garden",
    "steps": 5,
    "num_frames": 81
  }'

# Check status (replace JOB_ID with actual ID from above)
curl http://YOUR_POD_ID-8288.proxy.runpod.net/status/JOB_ID

# Download result when completed
curl -o result.mp4 http://YOUR_POD_ID-8288.proxy.runpod.net/download/JOB_ID
```

### 2. Python Example
```python
import requests
import time

# Generate video
response = requests.post('http://YOUR_POD_ID-8288.proxy.runpod.net/generate', json={
    "image": "https://picsum.photos/720/1280",
    "positive_prompt": "A beautiful landscape with flowing water",
    "steps": 5
})

job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# Monitor progress
while True:
    status_response = requests.get(f'http://YOUR_POD_ID-8288.proxy.runpod.net/status/{job_id}')
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        # Download result
        video_response = requests.get(f'http://YOUR_POD_ID-8288.proxy.runpod.net/download/{job_id}')
        with open('result.mp4', 'wb') as f:
            f.write(video_response.content)
        print("Video saved as result.mp4")
        break
    elif status in ["failed", "timeout"]:
        print("Job failed")
        break
    
    time.sleep(10)
```

### 3. Base64 Image Example
```python
import base64
import requests

# Read local image
with open('input.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

# Generate video
response = requests.post('http://YOUR_POD_ID-8288.proxy.runpod.net/generate', json={
    "image": f"data:image/jpeg;base64,{image_data}",
    "positive_prompt": "Epic cinematic scene",
    "width": 720,
    "height": 1280
})
```

## Parameters

- **image** (required): Image URL or base64 data URI
- **positive_prompt**: Text describing what you want in the video
- **negative_prompt**: Text describing what to avoid
- **width/height**: Video dimensions (must be multiples of 8)
- **num_frames**: Number of frames to generate (odd numbers work best)
- **steps**: Sampling steps (1-20, lower = faster)
- **cfg_scale**: Classifier-free guidance scale
- **seed**: Random seed (null for random)
- **model_name**: Model to use for generation

## Available Models

- **wan2.1_i2v_720p_14B_bf16.safetensors** (default) - 720p Image-to-Video, high quality
- **wan2.1_i2v_480p_14B_bf16.safetensors** - 480p Image-to-Video, faster generation
- **wan2.1_t2v_14B_bf16.safetensors** - Text-to-Video (for T2V workflows)
- **wan2.1_t2v_1.3B_bf16.safetensors** - Smaller T2V model, faster

## Notes

- Video generation takes 5-15 minutes depending on parameters
- Jobs are stored in memory (restarting the server clears job history)
- Maximum file upload size: 50MB
- Supported formats: JPG, PNG, WebP via URL or base64