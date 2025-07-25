#!/bin/bash
# Manual Flask API starter for current container

echo "🔍 Looking for Flask API file..."

# Find flask_api.py
FLASK_FILE=""
if [ -f "flask_api.py" ]; then
    FLASK_FILE="flask_api.py"
    echo "✅ Found Flask API at: ./flask_api.py"
elif [ -f "/flask_api.py" ]; then
    FLASK_FILE="/flask_api.py"
    echo "✅ Found Flask API at: /flask_api.py"
else
    echo "❌ Flask API file not found. Searching..."
    FLASK_FILE=$(find / -name "flask_api.py" 2>/dev/null | head -1)
    if [ -n "$FLASK_FILE" ]; then
        echo "✅ Found Flask API at: $FLASK_FILE"
    else
        echo "❌ Flask API not found anywhere"
        exit 1
    fi
fi

# Kill any existing Flask processes
echo "🛑 Stopping any existing Flask API processes..."
pkill -f flask_api.py

# Start Flask API
echo "🚀 Starting Flask API server on port 8288..."
mkdir -p /workspace
nohup python3 "$FLASK_FILE" > /workspace/flask_api_manual.log 2>&1 &
FLASK_PID=$!
echo "Flask API started (PID: $FLASK_PID)"

# Wait a moment and test
sleep 3
echo "🧪 Testing Flask API..."

# Test health endpoint
if curl -s -f http://localhost:8288/health > /dev/null; then
    echo "✅ Flask API is responding on port 8288!"
    echo "🔗 Available endpoints:"
    echo "  - Health: http://your-pod-url:8288/health"
    echo "  - Home: http://your-pod-url:8288/"
    echo "  - Generate: POST http://your-pod-url:8288/generate"
else
    echo "❌ Flask API not responding"
    echo "📝 Check logs: tail -f /workspace/flask_api_manual.log"
fi

echo ""
echo "📋 Flask API logs:"
tail -10 /workspace/flask_api_manual.log