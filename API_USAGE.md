# ComfyUI Wan Video Generation API

FastAPI ComfyUI Interface running on port 8189 for direct ComfyUI WebSocket API integration.

## Overview

The FastAPI ComfyUI Interface is a lightweight API server that provides direct integration with ComfyUI's native WebSocket API for workflow execution, job management, and output handling. It automatically loads the `Wrapper-SelfForcing-ImageToVideo-60FPS-API.json` workflow and accepts node updates through the prompt parameter.

## Configuration

### Environment Variables

- `COMFYUI_SERVER`: Connection to ComfyUI server (default: 127.0.0.1:8188)
- `FASTAPI_PORT`: API server port (default: 8189)
- `CLIENT_ID`: Unique client identifier for WebSocket connections

### Ports

- **ComfyUI**: http://localhost:8188 (Web UI)
- **FastAPI Interface**: http://localhost:8189 (REST API)
- **JupyterLab**: http://localhost:8888 (Development environment)

## Endpoints

### `GET /` - API Documentation
Returns API information and usage examples.

### `GET /docs` - Interactive API Documentation
Built-in FastAPI documentation for all available endpoints.

### `GET /health` - Health Check
Check if the API and ComfyUI are running.

```bash
curl http://YOUR_POD_ID-8189.proxy.runpod.net/health
```

### `GET /workflow/info` - Workflow Information
Get details about the loaded workflow including all node IDs and their parameters.

```bash
curl http://YOUR_POD_ID-8189.proxy.runpod.net/workflow/info
```

### `POST /generate` - Generate Video
Generate video using ComfyUI workflow with prompt updates.

**Request Body:**
```json
{
  "prompt": {
    "218": {
      "inputs": {
        "image": "https://example.com/image.jpg"
      },
      "class_type": "LoadImage"
    },
    "265": {
      "inputs": {
        "text": "A beautiful woman walking towards the camera"
      },
      "class_type": "Text Prompt (JPS)"
    },
    "266": {
      "inputs": {
        "text": "blurry, low quality, static"
      },
      "class_type": "Text Prompt (JPS)"
    },
    "205": {
      "inputs": {
        "steps": 5,
        "seed": 12345
      }
    },
    "215": {
      "inputs": {
        "generation_width": 720,
        "generation_height": 1280,
        "num_frames": 81
      }
    }
  },
  "webhook": "https://your-webhook.com/notify"
}
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "prompt_id": "comfyui_prompt_id",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

### `GET /status/<job_id>` - Check Job Status
Check the status of a video generation job.

```bash
curl http://YOUR_POD_ID-8189.proxy.runpod.net/status/JOB_ID
```

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "prompt_id": "comfyui_prompt_id",
  "status": "completed",
  "outputs": {
    "94": {
      "videos": [
        {
          "filename": "output_video.mp4",
          "subfolder": "",
          "type": "output"
        }
      ]
    }
  }
}
```

### `GET /download/<job_id>` - Download Result
Download the generated video file.

```bash
curl -o result.mp4 http://YOUR_POD_ID-8189.proxy.runpod.net/download/JOB_ID
```

### `GET /jobs` - List All Jobs
List all jobs and their statuses.

## Usage Examples

### 1. Basic cURL Example
```bash
# Generate video from URL
curl -X POST http://YOUR_POD_ID-8189.proxy.runpod.net/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "218": {
        "inputs": {
          "image": "https://picsum.photos/720/1280",
          "upload": "image"
        },
        "class_type": "LoadImage"
      }
    }
  }'

# Check status (replace JOB_ID with actual ID from above)
curl http://YOUR_POD_ID-8189.proxy.runpod.net/status/JOB_ID

# Download result when completed
curl -o result.mp4 http://YOUR_POD_ID-8189.proxy.runpod.net/download/JOB_ID
```

### 2. Python Example
```python
import requests
import time

# Generate video
response = requests.post('http://YOUR_POD_ID-8189.proxy.runpod.net/generate', json={
    "prompt": {
        "218": {
            "inputs": {
                "image": "https://picsum.photos/720/1280",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
    }
})

job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# Monitor progress
while True:
    status_response = requests.get(f'http://YOUR_POD_ID-8189.proxy.runpod.net/status/{job_id}')
    status = status_response.json()["status"]
    print(f"Status: {status}")
    
    if status == "completed":
        # Download result
        video_response = requests.get(f'http://YOUR_POD_ID-8189.proxy.runpod.net/download/{job_id}')
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
response = requests.post('http://YOUR_POD_ID-8189.proxy.runpod.net/generate', json={
    "prompt": {
        "218": {
            "inputs": {
                "image": f"data:image/jpeg;base64,{image_data}",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
    }
})
```

## Parameters

- **prompt** (required): ComfyUI workflow prompt object with node updates
- **webhook** (optional): Webhook URL for completion notifications

The prompt object should contain node ID keys with their respective inputs and class_type. See the workflow file `/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS-API.json` for the complete node structure.

## Available Models

- **wan2.1_i2v_720p_14B_bf16.safetensors** (default) - 720p Image-to-Video, high quality
- **wan2.1_i2v_480p_14B_bf16.safetensors** - 480p Image-to-Video, faster generation
- **wan2.1_t2v_14B_bf16.safetensors** - Text-to-Video (for T2V workflows)
- **wan2.1_t2v_1.3B_bf16.safetensors** - Smaller T2V model, faster

### LoRA Models

- `Wan21_CausVid_14B_T2V_lora_rank32.safetensors` - Causal video LoRA
- `Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors` - Distilled LoRA

## Workflow Usage

### Understanding the Workflow

The API loads the base workflow from `Wrapper-SelfForcing-ImageToVideo-60FPS-API.json` which contains:

- **Node 218**: LoadImage - Input image handling
- **Node 265**: Text Prompt (JPS) - Positive prompt
- **Node 266**: Text Prompt (JPS) - Negative prompt
- **Node 198**: WanVideoModelLoader - Model configuration
- **Node 205**: WanVideoSampler - Generation parameters
- **Node 215**: WanVideoImageClipEncode - Video size and frames
- **Node 94**: VHS_VideoCombine - Final 60FPS output
- **Node 270**: RIFE VFI - Frame interpolation

### Key Node Updates

You can update any node by providing its ID and new inputs:

```json
{
  "prompt": {
    "218": {"inputs": {"image": "your_image_url_or_base64"}},
    "265": {"inputs": {"text": "positive prompt"}},
    "266": {"inputs": {"text": "negative prompt"}},
    "205": {"inputs": {"steps": 5, "seed": 12345, "cfg": 1.0}},
    "215": {"inputs": {"generation_width": 720, "generation_height": 1280, "num_frames": 81}}
  }
}
```

## Advanced Features

### Webhook Notifications

Configure webhooks for job completion notifications by including a webhook URL in your request.

### Performance Optimization

- Use `enable_optimizations=true` for SageAttention support
- Monitor VRAM usage with `nvidia-smi`
- Use bf16 models for better memory efficiency

### Model Selection

- **High Quality**: 14B models (wan2.1_*_14B_bf16.safetensors)
- **Lower VRAM**: 1.3B models (wan2.1_t2v_1.3B_bf16.safetensors)
- **Speed**: Use distilled LoRAs for faster generation

## Error Handling

### Common Issues

1. **ComfyUI not ready**: Ensure ComfyUI is running on port 8188 before starting the API
2. **Model not found**: Check that required models are downloaded in `/workspace/ComfyUI/models/`
3. **Memory issues**: Use 1.3B models for lower VRAM systems

### Debugging

Check API logs:
```bash
tail -f /workspace/fastapi.log
```

Check ComfyUI logs:
```bash
tail -f /workspace/comfyui_*.log
```

## Notes

- Video generation takes 5-15 minutes depending on parameters
- Jobs are stored in memory (restarting the server clears job history)
- Uses direct ComfyUI WebSocket API for real-time status updates
- Workflow-based approach allows full ComfyUI functionality
- Built-in API documentation available at `/docs` endpoint