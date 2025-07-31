# Deployment Guide

## Build and Push to Docker Hub via GitHub Actions

### 1. Set up GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

- `DOCKERHUB_USERNAME`: Your Docker Hub username (szulic)
- `DOCKERHUB_TOKEN`: Your Docker Hub Personal Access Token

### 2. Trigger Build

The GitHub Actions will automatically build when you:

**Option A: Push to main/master branch**
```bash
git add .
git commit -m "Update ComfyUI setup"
git push origin main
```

**Option B: Create a version tag (recommended)**
```bash
git tag v1.0.0
git push origin v1.0.0
```

### 3. Monitor Build

- Go to your GitHub repository → Actions tab
- Watch the "Build and Push Docker Images to Docker Hub" workflow
- Build takes ~15-30 minutes due to model downloads

### 4. Use in RunPod

Once the build completes, your image will be available as:
`szulic/comfyui-wan:latest-wan`

## Local Testing (Optional)

```bash
# Build locally
./build.sh

# Test with docker-compose
docker-compose up

# Test services:
# - Jupyter: http://localhost:8888
# - ComfyUI: http://localhost:8188  
# - FastAPI Interface: http://localhost:8189
```

## RunPod Configuration

**Image**: `szulic/comfyui-wan:latest-wan`

**Ports to expose**:
- 8888 (Jupyter)
- 8188 (ComfyUI)
- 8189 (FastAPI ComfyUI Interface)

**Environment Variables**:
```
SERVE_API_LOCALLY=true
enable_optimizations=true
download_480p_native_models=true
download_720p_native_models=false
download_vace=false
change_preview_method=true
```

**GPU Requirements**:
- Minimum: RTX 4090 (24GB VRAM)
- Recommended: A100 (40GB+ VRAM)

## File Structure

```
comfyui-wan/
├── src/
│   ├── start.sh          # Main startup script
│   ├── comfyui_api.py    # FastAPI ComfyUI Interface
│   └── handler.py        # RunPod serverless handler
├── workflows/            # ComfyUI workflow files
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local development
├── build.sh              # Local build script
└── .github/workflows/    # GitHub Actions CI/CD
```

This maintains compatibility with the original Hearmeman24/comfyui-wan structure while adding the FastAPI ComfyUI Interface and proper Docker build automation.