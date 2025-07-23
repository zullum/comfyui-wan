# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based ComfyUI worker system optimized for Wan 2.1 video generation models. The project provides containerized deployment of ComfyUI with pre-configured models, custom nodes, and optimization features for video AI workflows.

## Development Commands

### Docker Operations
- **Build all images**: `docker buildx bake`
- **Build specific variant**: `docker buildx bake flux1-dev` (or base, sdxl, sd3, flux1-schnell)
- **Run locally**: `docker-compose up`
- **Access ComfyUI**: http://localhost:8188 (UI), http://localhost:8000 (API)

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
- ComfyUI installation via `comfy-cli`
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

The system builds multiple specialized Docker images:
- `base` - Clean ComfyUI without pre-downloaded models
- `sdxl` - Stable Diffusion XL models included
- `sd3` - Stable Diffusion 3 models included  
- `flux1-schnell` - FLUX.1 Schnell models included
- `flux1-dev` - FLUX.1 Dev models included

### Runtime Configuration

**Environment Variables**:
- `SERVE_API_LOCALLY=true` - Enable local API access
- `download_480p_native_models=true` - Download 480p models on startup
- `download_720p_native_models=true` - Download 720p models on startup
- `download_vace=true` - Download VACE enhancement models
- `enable_optimizations=false` - Toggle SageAttention optimizations
- `change_preview_method=true` - Enable video preview optimizations

**Startup Process**:
1. ComfyUI installation moved to workspace volume
2. Custom nodes updated (WanVideoWrapper, KJNodes)
3. Model downloads based on environment flags
4. SageAttention compilation (background)
5. JupyterLab and ComfyUI startup

### Workflow Management

Pre-configured workflows in `/workflows/`:
- Native T2V/I2V at 32FPS and 60FPS
- VACE reference image and outpainting workflows
- Wrapper-based workflows with self-forcing
- Fun ControlNet integration with SDXL helper
- Video extension and frame interpolation workflows

## Development Notes

**Multi-stage Docker Build**:
- Caching optimized with mount points
- Virtual environment isolation
- Parallel compilation with CMAKE_BUILD_PARALLEL_LEVEL=8

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