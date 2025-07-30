#!/bin/bash
"""
Installation script for ComfyUI Workflow Wrapper Service

This script installs the wrapper service dependencies and sets up the service.
"""

set -e  # Exit on any error

echo "Installing ComfyUI Workflow Wrapper Service..."

# Check if we're in a virtual environment or Docker
if [[ -n "$VIRTUAL_ENV" ]] || [[ -f /.dockerenv ]]; then
    echo "✓ Running in virtual environment or Docker"
else
    echo "⚠ Warning: Not in a virtual environment"
    echo "  Consider running: python -m venv venv && source venv/bin/activate"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements_wrapper.txt

echo "✓ Dependencies installed"

# Check if workflows directory exists
if [[ ! -d "../workflows" ]]; then
    echo "⚠ Warning: workflows directory not found at ../workflows"
    echo "  Make sure workflow JSON files are available"
else
    echo "✓ Workflows directory found"
    workflow_count=$(find ../workflows -name "*.json" | wc -l)
    echo "  Found $workflow_count workflow files"
fi

# Create systemd service file (optional)
if command -v systemctl &> /dev/null; then
    echo "Creating systemd service file..."
    
    cat > /tmp/comfyui-workflow-wrapper.service << EOF
[Unit]
Description=ComfyUI Workflow Wrapper Service
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=$(pwd)
Environment=PATH=$(which python | xargs dirname):${PATH}
Environment=COMFYUI_URL=http://127.0.0.1:8288
Environment=WRAPPER_PORT=8289
ExecStart=$(which python) workflow_wrapper.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    echo "  Service file created at /tmp/comfyui-workflow-wrapper.service"
    echo "  To install: sudo cp /tmp/comfyui-workflow-wrapper.service /etc/systemd/system/"
    echo "  To enable: sudo systemctl enable comfyui-workflow-wrapper"
    echo "  To start: sudo systemctl start comfyui-workflow-wrapper"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To start the service:"
echo "  python workflow_wrapper.py"
echo ""
echo "Service will be available at:"
echo "  http://localhost:8289"
echo ""
echo "API Documentation:"
echo "  http://localhost:8289/docs"
echo ""
echo "To test the service:"
echo "  python ../test_wrapper.py"