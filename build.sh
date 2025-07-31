#!/bin/bash

# Simple build script for local testing
echo "Building ComfyUI-Wan Docker image..."

docker build -t szulic/comfyui-wan:latest-wan .

echo "Build complete! You can now run:"
echo "docker-compose up"
echo ""
echo "Or directly:"
echo "docker run --gpus all -p 8188:8188 -p 8189:8189 szulic/comfyui-wan:latest-wan"