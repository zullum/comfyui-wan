#!/bin/bash
# Quick test script to fix ComfyUI frontend in running container

echo "🔧 Testing ComfyUI frontend fix..."

# Kill current ComfyUI
echo "Stopping current ComfyUI..."
pkill -f "main.py"

# Try to install ComfyUI frontend package
echo "Installing ComfyUI frontend..."
pip install --upgrade comfyui-frontend

# Check if ComfyUI has web directory
if [ ! -d "/workspace/ComfyUI/web" ]; then
    echo "⚠️  ComfyUI web directory missing. Attempting to restore..."
    
    # Try to create web directory with basic files
    mkdir -p /workspace/ComfyUI/web
    
    # Check if frontend package is available
    FRONTEND_PATH="/opt/venv/lib/python3.12/site-packages/comfyui_frontend_package/static"
    if [ -d "$FRONTEND_PATH" ]; then
        echo "✅ Frontend package found, creating symlink..."
        ln -sf "$FRONTEND_PATH" /workspace/ComfyUI/web/static
    else
        echo "❌ Frontend package not found. Need to rebuild image."
        exit 1
    fi
fi

# Restart ComfyUI from correct directory
echo "🚀 Restarting ComfyUI..."
cd /workspace/ComfyUI
nohup python3 main.py --listen 0.0.0.0 --use-sage-attention > /workspace/comfyui_test.log 2>&1 &

echo "✅ ComfyUI restarted. Check http://your-pod-url:8188"
echo "📋 Logs: tail -f /workspace/comfyui_test.log"