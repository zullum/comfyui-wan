#!/bin/bash

# RunPod Worker Setup Script
# This script runs during the Docker build phase for additional setup

echo "🔧 Running ComfyUI Wan Worker setup..."

# Ensure Python environment is ready
python -c "import runpod; print('✅ RunPod SDK ready')"
python -c "import requests; print('✅ Requests library ready')" 
python -c "import PIL; print('✅ Pillow ready')"
python -c "import boto3; print('✅ Boto3 ready')"

echo "✅ All dependencies verified successfully"
echo "🚀 ComfyUI Wan Worker build complete"