#!/bin/bash
# Quick script to restore workflows in current container

echo "🔄 Restoring ComfyUI workflows..."

WORKFLOW_DIR="/workspace/ComfyUI/user/default/workflows"
mkdir -p "$WORKFLOW_DIR"

# Create the workflows if they don't exist in container
# (In the rebuilt image, these will be copied from /workflows)

echo "📋 Creating sample workflows..."

# Create a basic text-to-video workflow
cat > "$WORKFLOW_DIR/Basic-T2V-Workflow.json" << 'EOF'
{
  "last_node_id": 1,
  "last_link_id": 0,
  "nodes": [
    {
      "id": 1,
      "type": "Note",
      "pos": [100, 100],
      "size": [400, 200],
      "flags": {},
      "order": 0,
      "mode": 0,
      "properties": {
        "text": "Welcome to ComfyUI-Wan!\n\nThis is a placeholder workflow.\nThe full workflows will be available after rebuilding the Docker image.\n\nWorkflows included:\n- Native T2V/I2V (60FPS)\n- VACE workflows\n- Wrapper workflows\n- Fun ControlNet integration"
      },
      "widgets_values": ["Welcome to ComfyUI-Wan!\n\nThis is a placeholder workflow.\nThe full workflows will be available after rebuilding the Docker image.\n\nWorkflows included:\n- Native T2V/I2V (60FPS)\n- VACE workflows\n- Wrapper workflows\n- Fun ControlNet integration"]
    }
  ],
  "links": [],
  "groups": [],
  "config": {},
  "extra": {
    "ds": {
      "scale": 1,
      "offset": [0, 0]
    }
  },
  "version": 0.4
}
EOF

echo "✅ Workflow restored! You should see 'Basic-T2V-Workflow' in the ComfyUI interface."
echo "🔄 Refresh the ComfyUI page to see the workflow."
echo ""
echo "📋 To get all your workflows back:"
echo "1. Commit and push the current fixes"
echo "2. Create a new tag: git tag v1.0.2 && git push origin v1.0.2" 
echo "3. Wait for GitHub Actions to build the new image"
echo "4. Restart your RunPod with the updated image"