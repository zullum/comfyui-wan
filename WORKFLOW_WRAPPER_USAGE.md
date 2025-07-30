# ComfyUI Workflow Wrapper Service

A dynamic wrapper service that solves the limitation of the ComfyUI API by providing:
- **Dynamic workflow loading** from JSON files
- **Simple parameter updates** without manual node mapping
- **Automatic node ID resolution** and workflow conversion
- **Job tracking and status monitoring**
- **Result download management**

## Overview

The ComfyUI API requires you to provide complete workflow structures with numbered nodes, making it difficult to dynamically update parameters. This wrapper service bridges that gap by:

1. Loading your existing ComfyUI workflow JSON files
2. Accepting simple parameter payloads (image, prompt, model, etc.)
3. Automatically mapping parameters to the correct node IDs
4. Converting to ComfyUI API format and submitting
5. Tracking job status and providing download URLs

## Quick Start

### 1. Start the Services

```bash
# Using Docker Compose (recommended)
docker-compose up

# Or manually in development
cd src
python workflow_wrapper.py
```

**Service URLs:**
- **Workflow Wrapper**: http://localhost:8289
- **API Documentation**: http://localhost:8289/docs
- **ComfyUI Web UI**: http://localhost:8188
- **ComfyUI API**: http://localhost:8288

### 2. Basic Usage

**Simple Image-to-Video Generation:**
```bash
curl -X POST http://localhost:8289/generate \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
    "node_updates": {
      "218": {"widgets_values": ["https://example.com/your-image.jpg", "image"]},
      "265": {"widgets_values": ["A beautiful woman walking towards the camera"]}
    }
  }'
```

**Response:**
```json
{
  "job_id": "12345678-1234-1234-1234-123456789abc",
  "status": "submitted",
  "prompt_id": "prompt_123",
  "message": "Workflow submitted successfully"
}
```

### 3. Track Job Status

```bash
curl http://localhost:8289/status/12345678-1234-1234-1234-123456789abc
```

### 4. Download Results

```bash
curl http://localhost:8289/download/12345678-1234-1234-1234-123456789abc
```

## API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and available workflows |
| `/workflows` | GET | List all available workflows |
| `/workflows/{name}` | GET | Get workflow details and node information |
| `/generate` | POST | Generate video with workflow parameters |
| `/status/{job_id}` | GET | Get job status and progress |
| `/download/{job_id}` | GET | Get download URLs for completed jobs |
| `/health` | GET | Health check and service status |

### Generate Video Parameters

```json
{
  "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
  "job_id": "optional-custom-id",
  "node_updates": {
    "218": {"widgets_values": ["https://example.com/image.jpg", "image"]},
    "265": {"widgets_values": ["Beautiful cinematic scene"]},
    "266": {"widgets_values": ["blurry, static, overexposed"]},
    "198": {"widgets_values": ["wan2.1_i2v_720p_14B_bf16.safetensors", "bf16", "fp8_e5m2", "offload_device", "sageattn"]},
    "205": {"widgets_values": [5, 1.0, 8.0, -1, "randomize", true, "unipc", 0, 1, "", "comfy"]}
  },
  "webhook": "https://your-webhook.com/notify",
  "convert_output": {
    "format": "mp4",
    "options": {"quality": "high"}
  }
}
```

**Required Parameters:**
- `workflow_name`: Name of workflow file (without .json extension)

**Optional Parameters:**
- `job_id`: Custom job identifier (auto-generated if not provided)
- `node_updates`: Dictionary of node IDs to update with new widget values
- `webhook`: URL for job completion notifications
- `convert_output`: Output format and options

**Node IDs for Wrapper-SelfForcing-ImageToVideo-60FPS:**
- `218`: LoadImage - `["image_path", "image"]`
- `265`: Text Prompt (Positive) - `["your positive prompt"]`
- `266`: Text Prompt (Negative) - `["your negative prompt"]`
- `198`: WanVideoModelLoader - `["model_name", "bf16", "fp8_e5m2", "offload_device", "sageattn"]`
- `205`: WanVideoSampler - `[steps, cfg, cfg_img, seed, "randomize", true, "unipc", 0, 1, "", "comfy"]`

## Available Workflows

The service automatically loads all workflow JSON files from the `workflows/` directory:

- **`Wrapper-SelfForcing-ImageToVideo-60FPS`** - Main I2V workflow with 60FPS output
- **`Legacy-Native-I2V-32FPS`** - Native I2V at 32FPS
- **`Legacy-Native-T2V-32FPS`** - Native T2V at 32FPS
- **`Native-I2V-60FPS`** - Native I2V at 60FPS
- **`Native-T2V-60FPS`** - Native T2V at 60FPS
- **`Legacy-VACE-Video-Reference`** - VACE reference workflow

Use `GET /workflows` to see all available workflows in your installation.

## Examples

### Python Client

```python
import requests
import time

class WorkflowClient:
    def __init__(self, base_url="http://localhost:8289"):
        self.base_url = base_url
    
    def generate_video(self, **params):
        response = requests.post(f"{self.base_url}/generate", json=params)
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = requests.get(f"{self.base_url}/status/{job_id}").json()
            if status['status'] == 'completed':
                return status
            time.sleep(5)
        raise TimeoutError("Job did not complete in time")

# Usage
client = WorkflowClient()

# Generate video
result = client.generate_video(
    workflow_name="Wrapper-SelfForcing-ImageToVideo-60FPS",
    image="https://picsum.photos/720/1280",
    positive_prompt="A serene lake with gentle waves",
    steps=5,
    seed=42
)

# Wait for completion
final_status = client.wait_for_completion(result['job_id'])
print(f"Video ready: {final_status}")
```

### cURL Examples

**List Available Workflows:**
```bash
curl http://localhost:8289/workflows
```

**Get Workflow Information:**
```bash
curl http://localhost:8289/workflows/Wrapper-SelfForcing-ImageToVideo-60FPS
```

**Advanced I2V Generation:**
```bash
curl -X POST http://localhost:8289/generate \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
    "job_id": "my-video-job-001",
    "image": "https://example.com/input.jpg",
    "positive_prompt": "A woman walking through a misty forest, cinematic lighting, 4K quality",
    "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清",
    "model_name": "wan2.1_i2v_720p_14B_bf16.safetensors",
    "steps": 5,
    "cfg": 1.0,
    "cfg_img": 8.0,
    "seed": 123456,
    "webhook": "https://my-webhook.com/comfyui-complete"
  }'
```

**Check Job Status:**
```bash
curl http://localhost:8289/status/my-video-job-001
```

**Download Results:**
```bash
# Get download URLs
curl http://localhost:8289/download/my-video-job-001

# Download the actual file
curl -o output.mp4 "http://localhost:8288/view?filename=ComfyUI_00001_.mp4&type=output"
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

class ComfyUIWrapper {
    constructor(baseURL = 'http://localhost:8289') {
        this.baseURL = baseURL;
        this.client = axios.create({ baseURL });
    }

    async generateVideo(params) {
        const response = await this.client.post('/generate', params);
        return response.data;
    }

    async getStatus(jobId) {
        const response = await this.client.get(`/status/${jobId}`);
        return response.data;
    }

    async waitForCompletion(jobId, timeout = 300000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            const status = await this.getStatus(jobId);
            
            if (status.status === 'completed') {
                return status;
            } else if (status.status === 'failed') {
                throw new Error(`Job failed: ${status.error}`);
            }
            
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
        
        throw new Error('Job timeout');
    }
}

// Usage
const wrapper = new ComfyUIWrapper();

async function generateVideo() {
    try {
        const result = await wrapper.generateVideo({
            workflow_name: 'Wrapper-SelfForcing-ImageToVideo-60FPS',
            image: 'https://picsum.photos/720/1280',
            positive_prompt: 'Beautiful sunset over mountains',
            steps: 5
        });
        
        console.log('Job submitted:', result.job_id);
        
        const finalStatus = await wrapper.waitForCompletion(result.job_id);
        console.log('Video complete:', finalStatus);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

generateVideo();
```

## Why You Need This Wrapper

**The Problem**: ComfyUI API requires you to send ALL ~50+ nodes from your workflow in every request. You can't just send a few nodes - it needs the complete workflow structure.

**The Solution**: This wrapper service:
1. Loads your complete workflow file
2. Updates only the specific nodes you want to change  
3. Sends the complete workflow to ComfyUI API

### Without Wrapper (Direct ComfyUI API)
```json
{
  "id": "job-123",
  "prompt": {
    "154": {"inputs": {"model_name": "4xLSDIR.pth"}, "class_type": "UpscaleModelLoader"},
    "155": {"inputs": {"UPSCALE_MODEL": ["154", 0]}, "class_type": "Anything Everywhere"},
    "161": {"inputs": {}, "class_type": "Note"},
    "198": {"inputs": {"model_name": "wan2.1_i2v_720p_14B_bf16.safetensors"}, "class_type": "WanVideoModelLoader"},
    "202": {"inputs": {"vae_name": "Wan2_1_VAE_bf16.safetensors"}, "class_type": "WanVideoVAELoader"},
    "205": {"inputs": {"steps": 5, "cfg": 1.0, "model": ["253", 0]}, "class_type": "WanVideoSampler"},
    "218": {"inputs": {"image": "image.jpg", "upload": "image"}, "class_type": "LoadImage"},
    "265": {"inputs": {"text": "A beautiful scene"}, "class_type": "Text Prompt (JPS)"},
    "266": {"inputs": {"text": "blurry, bad quality"}, "class_type": "Text Prompt (JPS)"},
    ... // 40+ more nodes with all connections
  }
}
```

### With Wrapper (Simple Update)
```json
{
  "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
  "node_updates": {
    "218": {"widgets_values": ["new-image.jpg", "image"]},
    "265": {"widgets_values": ["New positive prompt"]},
    "266": {"widgets_values": ["New negative prompt"]}
  }
}
```

**Result**: The wrapper loads your complete workflow, updates just these 3 nodes, and sends all 50+ nodes to ComfyUI API.

## Configuration

### Environment Variables

```bash
# ComfyUI API connection
export COMFYUI_URL="http://127.0.0.1:8288"

# Wrapper service port
export WRAPPER_PORT="8289"

# Workflows directory
export WORKFLOWS_DIR="/workspace/workflows"
```

### Docker Compose Integration

The wrapper service is automatically included in the Docker Compose setup:

```yaml
services:
  comfyui-worker:
    ports:
      - "8188:8188"  # ComfyUI Web UI
      - "8288:8288"  # ComfyUI API
      - "8289:8289"  # Workflow Wrapper
      - "8888:8888"  # JupyterLab
```

## Troubleshooting

### Common Issues

**1. Service Connection Errors**
```bash
# Check if services are running
curl http://localhost:8289/health

# Check logs
docker-compose logs comfyui-worker
# or
tail -f /workspace/workflow_wrapper.log
```

**2. Workflow Not Found**
```bash
# List available workflows
curl http://localhost:8289/workflows

# Check workflow directory
ls -la workflows/
```

**3. Job Stuck in Running State**
```bash
# Check ComfyUI API directly
curl http://localhost:8288/history/YOUR_JOB_ID

# Check ComfyUI logs
tail -f /workspace/comfyui_*.log
```

**4. Model Not Found Errors**
- Ensure required models are downloaded
- Check model names match exactly (case-sensitive)
- Verify models are in correct directories

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=debug
python workflow_wrapper.py
```

### Manual Testing

Test the wrapper service:
```bash
cd /path/to/comfyui-wan
python test_wrapper.py
```

## Advanced Features

### Webhook Notifications

Configure webhooks for job completion:
```json
{
  "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
  "image": "image.jpg",
  "webhook": "https://your-app.com/webhook/comfyui-complete"
}
```

The webhook will receive:
```json
{
  "job_id": "12345678-1234-1234-1234-123456789abc",
  "status": "completed",
  "outputs": {...},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Custom Output Formats

Specify output conversion:
```json
{
  "workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS",
  "image": "image.jpg",
  "convert_output": {
    "format": "mp4",
    "options": {
      "quality": "high",
      "codec": "h264",
      "bitrate": "8M"
    }
  }
}
```

### Batch Processing

Process multiple requests:
```python
import asyncio
import aiohttp

async def batch_generate(requests):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for req in requests:
            task = session.post('http://localhost:8289/generate', json=req)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]

# Generate multiple videos
requests = [
    {"workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS", "image": "img1.jpg"},
    {"workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS", "image": "img2.jpg"},
    {"workflow_name": "Wrapper-SelfForcing-ImageToVideo-60FPS", "image": "img3.jpg"}
]

results = asyncio.run(batch_generate(requests))
```

## Migration Guide

### From Direct ComfyUI API

1. **Replace endpoint**: Change from `:8288/prompt` to `:8289/generate`
2. **Simplify payload**: Use named parameters instead of node structure
3. **Update status checking**: Use `/status/{job_id}` instead of `/history/{prompt_id}`
4. **Update downloads**: Use `/download/{job_id}` to get URLs

### From Flask API

1. **Update port**: Change from 8288 to 8289 for the wrapper
2. **Update request format**: Use the new parameter structure
3. **Update response handling**: Job IDs and status format changed
4. **Update file handling**: Downloads now go through ComfyUI API

## Performance

- **Startup time**: ~2-3 seconds for service initialization
- **Request processing**: ~100-200ms for parameter mapping and conversion
- **Memory usage**: ~50MB additional overhead
- **Concurrent requests**: Supports multiple simultaneous requests

## Security

- **Input validation**: All parameters are validated before processing
- **Path traversal protection**: Workflow files are restricted to configured directory
- **Resource limits**: Prevents infinite loops and excessive memory usage
- **CORS support**: Configurable cross-origin request handling

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Full API docs at `/docs` endpoint
- **Logs**: Check `/workspace/workflow_wrapper.log` for detailed information
- **Health check**: Monitor service status at `/health` endpoint