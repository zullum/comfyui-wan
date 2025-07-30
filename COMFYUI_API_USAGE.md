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
POST http://localhost:8288/v1/queue/prompt
```

## Using the Wrapper Self-Forcing I2V 60FPS Workflow

### Basic Usage

To generate a 60FPS video from an image using the wrapper self-forcing workflow:

```bash
curl -X POST http://localhost:8288/v1/queue/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "input_image": {
        "inputs": {
          "image": "https://example.com/your-image.jpg",
          "upload": "image"
        },
        "class_type": "LoadImage"
      }
    }
  }'
```

### Advanced Configuration Example

```json
{
  "prompt": {
    "load_image": {
      "inputs": {
        "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
        "upload": "image"
      },
      "class_type": "LoadImage"
    },
    "text_prompt_positive": {
      "inputs": {
        "text": "A beautiful woman walking towards the camera, cinematic lighting, high quality"
      },
      "class_type": "TextPrompt"
    },
    "text_prompt_negative": {
      "inputs": {
        "text": "色调艳丽，过曝，静态，细节模糊不清, blurry, static, overexposed"
      },
      "class_type": "TextPrompt"
    },
    "wan_sampler": {
      "inputs": {
        "steps": 5,
        "cfg": 1.0,
        "cfg_img": 8.0,
        "seed": 42,
        "denoise": 1.0
      },
      "class_type": "WanVideoSampler"
    }
  },
  "client_id": "your-client-id"
}
```

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
GET http://localhost:8288/v1/history/{prompt_id}
```

### Downloading Results

Once complete, files are available via:

```bash
GET http://localhost:8288/v1/view?filename={output_filename}&subfolder=&type=output
```

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

Your existing `Wrapper-SelfForcing-ImageToVideo-60FPS.json` workflow can be used directly with the new API by posting it to the `/v1/queue/prompt` endpoint.

## Example Scripts

### Python Example

```python
import requests
import base64
import time

# Load and encode image
with open("input.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Submit workflow
response = requests.post("http://localhost:8288/v1/queue/prompt", json={
    "prompt": {
        "load_image": {
            "inputs": {
                "image": f"data:image/jpeg;base64,{image_data}",
                "upload": "image"
            },
            "class_type": "LoadImage"
        }
        # Add other workflow nodes here
    }
})

prompt_id = response.json()["prompt_id"]
print(f"Job submitted: {prompt_id}")

# Poll for completion
while True:
    status = requests.get(f"http://localhost:8288/v1/history/{prompt_id}")
    if status.status_code == 200 and status.json():
        print("Job completed!")
        break
    time.sleep(5)
```

### cURL Example

```bash
#!/bin/bash

# Submit a simple text-to-video job
curl -X POST http://localhost:8288/v1/queue/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "text_input": {
        "inputs": {
          "text": "A beautiful sunset over mountains"
        },
        "class_type": "TextPrompt"
      }
    }
  }'
```

## Support

For issues with the ComfyUI API server, check:
- [ComfyUI API GitHub](https://github.com/SaladTechnologies/comfyui-api)
- API documentation at `http://localhost:8288/docs`
- ComfyUI logs for workflow-specific issues