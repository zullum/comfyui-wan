# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based ComfyUI worker system optimized for Wan 2.1 video generation models. The project provides containerized deployment of ComfyUI with pre-configured models, custom nodes, and optimization features for video AI workflows.

## Development Commands

### Docker Operations
- **Build all images**: `docker buildx bake`
- **Build specific variant**: `docker buildx bake wan` (or base)
- **Run locally**: `docker-compose up`
- **Access services**: 
  - ComfyUI Web UI: http://localhost:8188
  - ComfyUI API: http://localhost:8288 (SaladTechnologies API)
  - JupyterLab: http://localhost:8888

### RunPod Serverless
- **Install dependencies**: `pip install -r builder/requirements.txt`
- **Test handler locally**: `cd src && python handler.py --rp_serve_api`
- **Build verification**: `bash builder/setup.sh`

### Model Management
- **Download CivitAI models**: `python src/download.py -m MODEL_ID [-t TOKEN]`
- **Environment variables**: Set `civitai_token` for automatic authentication

## Architecture Overview

### Core Components

**Container Structure**:
- Base image: NVIDIA CUDA 12.8.1 with Ubuntu 24.04
- ComfyUI installation directly from GitHub
- SaladTechnologies ComfyUI API binary (replaces Flask API)
- Node.js 20.x LTS for API server runtime
- Pre-installed custom nodes for video processing
- JupyterLab environment for development
- Optimized memory management with tcmalloc

**Model Organization**:
- `/ComfyUI/models/diffusion_models/` - Main Wan 2.1 models (480p/720p variants)
- `/ComfyUI/models/text_encoders/` - UMT5 and CLIP encoders
- `/ComfyUI/models/vae/` - Video Auto-Encoders
- `/ComfyUI/models/loras/` - LoRA optimization models
- `/ComfyUI/models/upscale_models/` - Post-processing upscalers

**Key Custom Nodes**:
- ComfyUI-WanVideoWrapper - Core Wan integration
- ComfyUI-KJNodes - Video processing utilities
- ComfyUI-VideoHelperSuite - Video I/O operations
- Multiple others for UI, effects, and workflow enhancement

### Deployment Variants

The system builds Docker images via docker-bake.hcl:
- `base` - Clean ComfyUI base installation
- `wan` - Complete Wan 2.1 video generation setup (default)

### Runtime Configuration

**Environment Variables**:
- `SERVE_API_LOCALLY=true` - Enable local API access
- `download_480p_native_models=true` - Download 480p models on startup
- `download_720p_native_models=true` - Download 720p models on startup
- `download_vace=true` - Download VACE enhancement models
- `enable_optimizations=false` - Toggle SageAttention optimizations
- `change_preview_method=true` - Enable video preview optimizations
- `COMFYUI_URL=http://127.0.0.1:8188` - ComfyUI API connection
- `PORT=8288` - ComfyUI API server port
- `LOG_LEVEL=info` - API logging level

**Startup Process**:
1. ComfyUI installation moved to workspace volume
2. Custom nodes updated (WanVideoWrapper, KJNodes)
3. Model downloads based on environment flags
4. SageAttention compilation (background)
5. ComfyUI API server startup on port 8288
6. JupyterLab and ComfyUI startup

### API Architecture

**Dual-Mode Operation**:
- **Pod Mode**: Full development environment with ComfyUI Web UI and API
- **Serverless Mode**: RunPod serverless handler (`src/handler.py`) with optimized workflow execution

**API Endpoints**:
- **ComfyUI API**: Port 8288 - Production-ready REST API with Swagger docs at `/docs`
- **RunPod Handler**: Serverless execution of `Wrapper-SelfForcing-ImageToVideo-60FPS` workflow
- **Direct ComfyUI**: Port 8188 - Native ComfyUI WebSocket API

**Request Flow**:
1. Input validation and image preprocessing
2. ComfyUI workflow execution via native API
3. Video generation with frame interpolation
4. Output handling (S3 upload or base64 encoding)

### Workflow Management

Pre-configured workflows in `/workflows/`:
- `Wrapper-SelfForcing-ImageToVideo-60FPS.json` - Main I2V workflow with RIFE interpolation
- Native T2V/I2V workflows at various frame rates
- VACE reference image and outpainting workflows
- Fun ControlNet integration with SDXL helper

## Project Structure

**Key Directories**:
- `src/` - Source code and startup scripts
  - `handler.py` - RunPod serverless handler with workflow execution
  - `start.sh` - Main container startup script with model downloads
  - `download.py` - CivitAI model download utility
- `workflows/` - ComfyUI workflow JSON files
- `builder/` - Build-time dependencies and setup scripts
- `docker-bake.hcl` - Multi-target Docker build configuration

**Critical Files**:
- `Dockerfile` - Multi-stage build with CUDA base, Node.js, and ComfyUI API
- `docker-compose.yml` - Local development environment
- `COMFYUI_API_USAGE.md` - Comprehensive API documentation and examples

**Build Architecture**:
- **Base stage**: CUDA environment with Python virtual environment
- **Final stage**: Complete application with models and custom nodes
- **Docker Bake**: Supports `base` and `wan` variants

## Development Notes

**Multi-stage Docker Build**:
- Caching optimized with mount points
- Virtual environment isolation
- Parallel compilation with CMAKE_BUILD_PARALLEL_LEVEL=8
- Node.js 20.x LTS installation for ComfyUI API

**API Integration**:
- SaladTechnologies ComfyUI API replaces Flask implementation
- Native ComfyUI workflow compatibility
- Production-ready job queue and status tracking
- Built-in Swagger documentation

**GPU Requirements**:
- NVIDIA GPU with CUDA 12.8+ support
- Minimum 24GB VRAM recommended for 14B models
- 1.3B models available for lower VRAM systems

**Storage Considerations**:
- Base models: 10-28GB each (14B variants)
- Text encoders: 2-5GB each
- VAE models: 1-3GB each
- Total storage: 50-100GB for full installation

**Performance Optimizations**:
- SageAttention for memory-efficient attention
- tcmalloc for improved memory management
- Parallel aria2c downloads with corruption checking
- Background model compilation during startup