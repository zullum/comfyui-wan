#!/bin/bash

# ComfyUI Workflow Trigger Script
# Usage: ./trigger_workflow.sh [IMAGE_PATH] [PROMPT] [OUTPUT_NAME]

# Default values
COMFYUI_URL="http://localhost:8188"
IMAGE_PATH="${1:-input_image.jpg}"
PROMPT="${2:-A beautiful woman walking towards the camera}"
OUTPUT_NAME="${3:-output_video}"
WORKFLOW_FILE="workflows/Wrapper-SelfForcing-ImageToVideo-60FPS.json"

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "Error: Workflow file $WORKFLOW_FILE not found!"
    exit 1
fi

# Check if image exists
if [ ! -f "$IMAGE_PATH" ]; then
    echo "Error: Image file $IMAGE_PATH not found!"
    exit 1
fi

# Copy image to ComfyUI input directory (if running locally)
if [ -d "ComfyUI/input" ]; then
    cp "$IMAGE_PATH" "ComfyUI/input/"
    echo "✅ Copied image to ComfyUI input directory"
fi

echo "🚀 Triggering ComfyUI workflow..."
echo "📷 Image: $IMAGE_PATH"
echo "💭 Prompt: $PROMPT"
echo "📝 Output: $OUTPUT_NAME"
echo "🌐 ComfyUI URL: $COMFYUI_URL"

# Read workflow and modify parameters
WORKFLOW_JSON=$(cat "$WORKFLOW_FILE")

# Create the API request payload
PAYLOAD=$(jq -n \
  --argjson workflow "$WORKFLOW_JSON" \
  --arg image "$(basename "$IMAGE_PATH")" \
  --arg prompt "$PROMPT" \
  '{
    "prompt": $workflow,
    "client_id": "terminal_client"
  }')

# Send request to ComfyUI
RESPONSE=$(curl -s -X POST "$COMFYUI_URL/prompt" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

# Check if request was successful
if echo "$RESPONSE" | jq -e '.prompt_id' > /dev/null; then
    PROMPT_ID=$(echo "$RESPONSE" | jq -r '.prompt_id')
    echo "✅ Workflow submitted successfully!"
    echo "🔍 Prompt ID: $PROMPT_ID"
    echo "📊 Monitor progress at: $COMFYUI_URL"
    echo "📈 Check status: curl $COMFYUI_URL/history/$PROMPT_ID"
    
    # Optional: Monitor progress
    if [ "$4" = "--monitor" ]; then
        echo "🔄 Monitoring progress..."
        while true; do
            STATUS=$(curl -s "$COMFYUI_URL/history/$PROMPT_ID")
            if echo "$STATUS" | jq -e ".$PROMPT_ID" > /dev/null; then
                echo "✅ Workflow completed!"
                echo "📁 Check output directory for results"
                break
            fi
            echo "⏳ Still processing..."
            sleep 5
        done
    fi
else
    echo "❌ Failed to submit workflow!"
    echo "Response: $RESPONSE"
    exit 1
fi