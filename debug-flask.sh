#!/bin/bash
# Debug Flask API connectivity

echo "🔍 Debugging Flask API on port 8288..."

# Check if Flask process is running
echo "📋 Checking Flask processes:"
ps aux | grep flask_api || echo "❌ No Flask API process found"

# Check if port 8288 is in use
echo ""
echo "🔌 Checking port 8288:"
netstat -tlnp | grep 8288 || echo "❌ Port 8288 not listening"

# Check Flask API log file
echo ""
echo "📝 Flask API logs:"
if [ -f "/workspace/flask_api.log" ]; then
    echo "Last 20 lines of Flask API log:"
    tail -20 /workspace/flask_api.log
else
    echo "❌ Flask API log file not found"
fi

# Try to start Flask API manually for testing
echo ""
echo "🧪 Testing Flask API startup:"
cd /
if [ -f "/comfyui-wan/src/flask_api.py" ]; then
    echo "✅ Flask API file found at /comfyui-wan/src/flask_api.py"
    echo "🚀 Starting Flask API manually..."
    timeout 10 python3 /comfyui-wan/src/flask_api.py &
    sleep 3
    
    # Test if it's responding
    echo "🔗 Testing API connectivity:"
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8288/health || echo "❌ Cannot connect to Flask API"
    
    # Kill the test process
    pkill -f flask_api.py
elif [ -f "flask_api.py" ]; then
    echo "✅ Flask API file found at ./flask_api.py"
    timeout 10 python3 flask_api.py &
    sleep 3
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8288/health || echo "❌ Cannot connect to Flask API"
    pkill -f flask_api.py
else
    echo "❌ Flask API file not found"
    find / -name "flask_api.py" 2>/dev/null | head -5
fi

echo ""
echo "🔧 Manual Flask API test complete"