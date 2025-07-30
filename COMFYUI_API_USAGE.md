# ComfyUI API Usage Guide

This document provides comprehensive instructions for using the ComfyUI API server that replaces the Flask API in this ComfyUI Wan video generation setup.

## Overview

The ComfyUI API (by SaladTechnologies) is a production-ready API server that provides full ComfyUI functionality with additional conveniences for workflow execution, job management, and output handling.

## Configuration

### Environment Variables

The following environment variables are configured in the Docker setup:

- `COMFYUI_URL`: Connection to ComfyUI server (default: http://127.0.0.1:8188)
- `PORT`: API server port (default: 8288)  
- `LOG_LEVEL`: Logging level (default: info)
- `SYNC_OUTPUT`: Enable synchronous output (default: true)
- `OUTPUT_PATH`: Output file path (default: /workspace/ComfyUI/output)

### Ports

- **ComfyUI**: http://localhost:8188 (Web UI)
- **ComfyUI API**: http://localhost:8288 (REST API)
- **JupyterLab**: http://localhost:8888 (Development environment)

## API Endpoints

### Health Check
```bash
GET http://localhost:8288/health
```

### API Documentation
```bash
GET http://localhost:8288/docs
```
Interactive Swagger documentation for all available endpoints.

### Execute Workflow
```bash
POST http://localhost:8288/prompt
```

## Using the Wrapper Self-Forcing I2V 60FPS Workflow

### Important: API Request Format

The ComfyUI API expects a specific format where the `prompt` field contains a JSON object with numbered node IDs. Each node must have `inputs` and `class_type` fields.

### Basic Usage

To use your existing workflow file directly:

```bash
# First, load your workflow JSON and modify the LoadImage node
curl -X POST http://localhost:8288/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "id": "unique-request-id",
    "prompt": {
      "218": {
        "inputs": {
          "image": "https://example.com/your-image.jpg",
          "upload": "image"
        },
        "class_type": "LoadImage"
      }
    },
    "webhook": "https://your-webhook.com/notify"
  }'
```

**Note**: The above example shows only the LoadImage node. For a complete workflow, you need to include all nodes from your `Wrapper-SelfForcing-ImageToVideo-60FPS.json` file.

### Complete Workflow Example

For a full I2V workflow, you would need to convert your ComfyUI workflow file to the API format. Here's a simplified example structure:

```json
{
  "id": "12345678-1234-1234-1234-123456789abc",
  "prompt": {
    "1": {
      "inputs": {
        "image": "https://example.com/input.jpg",
        "upload": "image"
      },
      "class_type": "LoadImage"
    },
    "2": {
      "inputs": {
        "text": "A beautiful woman walking towards the camera"
      },
      "class_type": "CLIPTextEncode"
    },
    "3": {
      "inputs": {
        "text": "色调艳丽，过曝，静态，细节模糊不清"
      },
      "class_type": "CLIPTextEncode"
    },
    "4": {
      "inputs": {
        "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"
      },
      "class_type": "WanVideoModelLoader"
    },
    "5": {
      "inputs": {
        "steps": 5,
        "cfg": 1.0,
        "cfg_img": 8.0,
        "seed": ["6", 0],
        "model": ["4", 0],
        "positive": ["2", 0],
        "negative": ["3", 0],
        "image": ["1", 0]
      },
      "class_type": "WanVideoSampler"
    },
    "6": {
      "inputs": {
        "seed": -1
      },
      "class_type": "Seed"
    }
  },
  "webhook": "https://your-webhook-url.com/notify",
  "convert_output": {
    "format": "mp4",
    "options": {
      "quality": "high"
    }
  }
}

### Response Format

The API returns a job ID that you can use to track progress:

```json
{
  "prompt_id": "12345678-1234-1234-1234-123456789abc",
  "number": 1,
  "node_errors": {}
}
```

### Checking Job Status

```bash
GET http://localhost:8288/history/{prompt_id}
```

### Downloading Results

Once complete, files are available via:

```bash
GET http://localhost:8288/view?filename={output_filename}&subfolder=&type=output
```

### Using Your Existing Workflow File

The easiest way to use the API is to load your existing `Wrapper-SelfForcing-ImageToVideo-60FPS.json` workflow and extract the `prompt` section. The workflow file contains a `workflow` object that needs to be converted to the API format.

**Conversion Process**:
1. Load your workflow JSON file
2. Extract the relevant nodes and their connections
3. Convert to the numbered node format expected by the API
4. Replace image inputs with your image URL or base64 data

## Workflow Configuration Examples

### Basic I2V Parameters

```json
{
  "positive_prompt": "A beautiful scene with natural lighting",
  "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清",
  "width": 720,
  "height": 1280,
  "num_frames": 81,
  "steps": 5,
  "cfg_scale": 1.0,
  "cfg_img": 8.0,
  "seed": -1,
  "lora_strength": 0.7,
  "frame_rate": 16,
  "interpolation_multiplier": 5,
  "final_frame_rate": 60,
  "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"
}
```

### Available Models

- `wan2.1_i2v_720p_14B_bf16.safetensors` - 720p Image-to-Video (14B parameters)
- `wan2.1_i2v_480p_14B_bf16.safetensors` - 480p Image-to-Video (14B parameters)  
- `wan2.1_t2v_14B_bf16.safetensors` - Text-to-Video (14B parameters)
- `wan2.1_t2v_1.3B_bf16.safetensors` - Text-to-Video (1.3B parameters)

### LoRA Models

- `Wan21_CausVid_14B_T2V_lora_rank32.safetensors` - Causal video LoRA
- `Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors` - Distilled LoRA

## Advanced Features

### Webhook Notifications

Configure webhooks for job completion notifications:

```bash
export WEBHOOK_URL="https://your-webhook-endpoint.com/notify"
```

### S3 Output Storage

Configure S3 for output storage:

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
export S3_BUCKET_NAME="your-output-bucket"
```

### Synchronous vs Asynchronous Processing

For immediate results (smaller workloads):
```bash
export SYNC_OUTPUT=true
```

For background processing (larger workloads):
```bash
export SYNC_OUTPUT=false
```

## Error Handling

### Common Issues

1. **ComfyUI not ready**: Ensure ComfyUI is running on port 8188 before starting the API
2. **Model not found**: Check that required models are downloaded in `/workspace/ComfyUI/models/`
3. **Memory issues**: Use 1.3B models for lower VRAM systems

### Debugging

Check API logs:
```bash
tail -f /workspace/comfyui_api.log
```

Check ComfyUI logs:
```bash
tail -f /workspace/comfyui_*.log
```

## Performance Optimization

### GPU Memory Management

- Use `enable_optimizations=true` for SageAttention support
- Monitor VRAM usage with `nvidia-smi`
- Use bf16 models for better memory efficiency

### Model Selection

- **High Quality**: 14B models (wan2.1_*_14B_bf16.safetensors)
- **Lower VRAM**: 1.3B models (wan2.1_t2v_1.3B_bf16.safetensors)
- **Speed**: Use distilled LoRAs for faster generation

## Migration from Flask API

### Key Differences

1. **Port**: Same port 8288 maintained for compatibility
2. **Request format**: Now uses ComfyUI native workflow format
3. **Response format**: Returns ComfyUI-standard prompt_id and job tracking
4. **File handling**: Direct integration with ComfyUI's file system
5. **Documentation**: Built-in Swagger docs at `/docs`

### Workflow Conversion

Your existing `Wrapper-SelfForcing-ImageToVideo-60FPS.json` workflow can be used directly with the new API by converting it to the proper format and posting it to the `/prompt` endpoint.

## Example Scripts

### Python Example

```python
import requests
import base64
import time
import json

# Load and encode image
with open("input.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Load your existing workflow (you'll need to convert it to API format)
# This is a simplified example - use your actual workflow structure
payload = {
    "id": "my-video-generation-job",
    "prompt": {
        "1": {
            "inputs": {
                "image": f"data:image/jpeg;base64,{image_data}",
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        "2": {
            "inputs": {
                "text": "A beautiful woman walking towards the camera"
            },
            "class_type": "CLIPTextEncode"
        }
        # Add all other nodes from your workflow here
    },
    "webhook": "https://your-webhook.com/notify"  # Optional
}

# Submit workflow
response = requests.post("http://localhost:8288/prompt", json=payload)
result = response.json()
prompt_id = result["prompt_id"]
print(f"Job submitted: {prompt_id}")

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8288/history/{prompt_id}")
    if status.status_code == 200:
        history = status.json()
        if prompt_id in history and "outputs" in history[prompt_id]:
            print("Job completed!")
            # Extract output files
            outputs = history[prompt_id]["outputs"]
            for node_id, node_output in outputs.items():
                if "videos" in node_output:
                    for video in node_output["videos"]:
                        video_url = f"http://localhost:8288/view?filename={video['filename']}&type=output"
                        print(f"Video available at: {video_url}")
            break
    time.sleep(5)
```

### cURL Example

```bash
#!/bin/bash

# Submit a simple image-to-video job
curl -X POST http://localhost:8288/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "id": "curl-test-job",
    "prompt": {
      "1": {
        "inputs": {
          "image": "https://example.com/your-image.jpg",
          "upload": "image"
        },
        "class_type": "LoadImage"
      },
      "2": {
        "inputs": {
          "text": "A beautiful sunset over mountains"
        },
        "class_type": "CLIPTextEncode"
      }
    },
    "webhook": "https://your-webhook.com/notify"
  }'

# Check status (replace PROMPT_ID with the returned prompt_id)
curl -X GET "http://localhost:8288/history/PROMPT_ID"

# Download result video (replace FILENAME with actual filename from history)
curl -X GET "http://localhost:8288/view?filename=FILENAME&type=output" -o output_video.mp4
```

## Support

For issues with the ComfyUI API server, check:
- [ComfyUI API GitHub](https://github.com/SaladTechnologies/comfyui-api)
- API documentation at `http://localhost:8288/docs`
- ComfyUI logs for workflow-specific issues