#!/bin/bash
echo "🚀 Starting ComfyUI Wan setup..."
echo "📂 Working directory: $(pwd)"
echo "📋 Files available: $(ls -la)"

# The start.sh script should be in the current directory since we copied src/* to root
if [ -f "./start.sh" ]; then
    echo "✅ Found local start.sh, executing..."
    bash ./start.sh
else
    echo "❌ start.sh not found in current directory"
    echo "📋 Available files:"
    ls -la
    exit 1
fi