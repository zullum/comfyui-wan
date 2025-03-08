#!/usr/bin/env bash

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# This is in case there's any special installs or overrides that needs to occur when starting the machine before starting ComfyUI
if [ -f "/workspace/additional_params.sh" ]; then
    chmod +x /workspace/additional_params.sh
    echo "Executing additional_params.sh..."
    /workspace/additional_params.sh
else
    echo "additional_params.sh not found in /workspace. Skipping..."
fi

# Set the network volume path
NETWORK_VOLUME="/workspace"

# Check if NETWORK_VOLUME exists; if not, use root directory instead
if [ ! -d "$NETWORK_VOLUME" ]; then
    echo "NETWORK_VOLUME directory '$NETWORK_VOLUME' does not exist. You are NOT using a network volume. Setting NETWORK_VOLUME to '/' (root directory)."
    NETWORK_VOLUME="/"
    echo "NETWORK_VOLUME directory doesn't exist. Starting JupyterLab on root directory..."
    jupyter-lab --ip=0.0.0.0 --allow-root --no-browser --NotebookApp.token='' --NotebookApp.password='' --ServerApp.allow_origin='*' --ServerApp.allow_credentials=True --notebook-dir=/ &
else
    echo "NETWORK_VOLUME directory exists. Starting JupyterLab..."
    jupyter-lab --ip=0.0.0.0 --allow-root --no-browser --NotebookApp.token='' --NotebookApp.password='' --ServerApp.allow_origin='*' --ServerApp.allow_credentials=True --notebook-dir=/workspace &
fi

COMFYUI_DIR="$NETWORK_VOLUME/ComfyUI"
WORKFLOW_DIR="$NETWORK_VOLUME/ComfyUI/user/default/workflows"

# Set the target directory
CUSTOM_NODES_DIR="$NETWORK_VOLUME/ComfyUI/custom_nodes"

if [ ! -d "$COMFYUI_DIR" ]; then
    mv /ComfyUI "$COMFYUI_DIR"
else
    echo "Directory already exists, skipping move."
fi

echo "Downloading CivitAI download script to /usr/local/bin"
git clone "https://github.com/Hearmeman24/CivitAI_Downloader.git" || { echo "Git clone failed"; exit 1; }
mv CivitAI_Downloader/download.py "/usr/local/bin/" || { echo "Move failed"; exit 1; }
chmod +x "/usr/local/bin/download.py" || { echo "Chmod failed"; exit 1; }
rm -rf CivitAI_Downloader  # Clean up the cloned repo

# Change to the directory
cd "$CUSTOM_NODES_DIR" || exit 1

if [ "$download_quantized_model" == "true" ]; then
  mkdir -p "$NETWORK_VOLUME/ComfyUI/models/diffusion_models"
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors" \
      https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-T2V-14B_fp8_e4m3fn.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/Wan2_1-I2V-14B-720P_fp8_e4m3fn.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/Wan2_1-I2V-14B-720P_fp8_e4m3fn.safetensors" \
      https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1-I2V-14B-720P_fp8_e4m3fn.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors
  fi
fi
if [ "$download_480p_native_models" == "true" ]; then
  mkdir -p "$NETWORK_VOLUME/ComfyUI/models/diffusion_models"
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_i2v_480p_14B_bf16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_i2v_480p_14B_bf16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_480p_14B_bf16.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors
  fi
fi
if [ "$download_720p_native_models" == "true" ]; then
  mkdir -p "$NETWORK_VOLUME/ComfyUI/models/diffusion_models"
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_i2v_720p_14B_bf16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_i2v_720p_14B_bf16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_i2v_720p_14B_bf16.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_14B_bf16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_14B_bf16.safetensors
  fi
  if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" ]; then
      wget -c -O "$NETWORK_VOLUME/ComfyUI/models/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors" \
      https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_fp16.safetensors
  fi
fi

echo "Downloading text encoders"
mkdir -p "$NETWORK_VOLUME/ComfyUI/models/text_encoders"
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/text_encoders/umt5-xxl-enc-bf16.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/text_encoders/umt5-xxl-enc-bf16.safetensors" \
    https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
    https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/text_encoders/open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/text_encoders/open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors" \
    https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/clip_vision/clip_vision_h.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/clip_vision/clip_vision_h.safetensors" \
    https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors
fi

echo "Downloading VAE"
mkdir -p "$NETWORK_VOLUME/ComfyUI/models/vae"
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/vae/Wan2_1_VAE_bf16.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/vae/Wan2_1_VAE_bf16.safetensors" \
    https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan2_1_VAE_bf16.safetensors
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/vae/wan_2.1_vae.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/vae/wan_2.1_vae.safetensors" \
    https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors
fi

# Download upscale model
echo "Downloading upscale models"
mkdir -p "$NETWORK_VOLUME/ComfyUI/models/upscale_models"
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/upscale_models/4x_foolhardy_Remacri.pt" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/upscale_models/4x_foolhardy_Remacri.pt" \
    https://huggingface.co/FacehugmanIII/4x_foolhardy_Remacri/resolve/main/4x_foolhardy_Remacri.pth
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/upscale_models/OmniSR_X2_DIV2K.safetensors" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/upscale_models/OmniSR_X2_DIV2K.safetensors" \
    https://huggingface.co/Acly/Omni-SR/resolve/main/OmniSR_X2_DIV2K.safetensors
fi
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/upscale_models/4xLSDIR.pth" ]; then
    if [ -f "/4xLSDIR.pth" ]; then
        mv "/4xLSDIR.pth" "$NETWORK_VOLUME/ComfyUI/models/upscale_models/4xLSDIR.pth"
        echo "Moved 4xLSDIR.pth to the correct location."
    else
        echo "4xLSDIR.pth not found in the root directory."
    fi
else
    echo "4xLSDIR.pth already exists. Skipping."
fi

# Download film network model
echo "Downloading film network model"
if [ ! -f "$NETWORK_VOLUME/ComfyUI/models/upscale_models/film_net_fp32.pt" ]; then
    wget -O "$NETWORK_VOLUME/ComfyUI/models/upscale_models/film_net_fp32.pt" \
    https://huggingface.co/nguu/film-pytorch/resolve/887b2c42bebcb323baf6c3b6d59304135699b575/film_net_fp32.pt
fi

echo "Finished downloading models!"


echo "Checking and copying workflow..."
mkdir -p "$WORKFLOW_DIR"

# Ensure the file exists in the current directory before moving it
cd /

WORKFLOWS=("Wan_Video_Image2Video-Upscaling_FrameInterpolation.json" "Wan_Video_Text2Video-Upscaling_FrameInterpolation.json" "Wan_Video_Video2Video-Upscaling_FrameInterpolation.json" "Native_ComfyUI_Wan_Video_Image2Video-Upscaling_FrameInterpolation.json" "Native_ComfyUIWan_Video_Text2Video-Upscaling_FrameInterpolation.json")

for WORKFLOW in "${WORKFLOWS[@]}"; do
    if [ -f "./$WORKFLOW" ]; then
        if [ ! -f "$WORKFLOW_DIR/$WORKFLOW" ]; then
            mv "./$WORKFLOW" "$WORKFLOW_DIR"
            echo "$WORKFLOW copied."
        else
            echo "$WORKFLOW already exists in the target directory, skipping move."
        fi
    else
        echo "$WORKFLOW not found in the current directory."
    fi
done

declare -A MODEL_CATEGORIES=(
    ["$NETWORK_VOLUME/ComfyUI/models/checkpoints"]="$CHECKPOINT_IDS_TO_DOWNLOAD"
    ["$NETWORK_VOLUME/ComfyUI/models/loras"]="$LORAS_IDS_TO_DOWNLOAD"
)

# Ensure directories exist and download models
for TARGET_DIR in "${!MODEL_CATEGORIES[@]}"; do
    mkdir -p "$TARGET_DIR"
    IFS=',' read -ra MODEL_IDS <<< "${MODEL_CATEGORIES[$TARGET_DIR]}"

    for MODEL_ID in "${MODEL_IDS[@]}"; do
        echo "Downloading model: $MODEL_ID to $TARGET_DIR"
        (cd "$TARGET_DIR" && download.py --model "$MODEL_ID")
    done
done

if ["$change_preview_method" == "true"]; then
    echo "Updating default preview method..."
    sed -i '/def get_current_preview_method()/,/^    return /s/return "none"/return "auto"/' $NETWORK_VOLUME/ComfyUI/custom_nodes/ComfyUI-Manager/glob/manager_core.py
    sed -i '/id: *'"'"'VHS.LatentPreview'"'"'/,/defaultValue:/s/defaultValue: false/defaultValue: true/' $NETWORK_VOLUME/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite/web/js/VHS.core.js
    echo "Default preview method updated to 'auto'"
else
    echo "Skipping preview method update (CHANGE_PREVIEW_METHOD is not 'true')."
fi

# Workspace as main working directory
echo "cd $NETWORK_VOLUME" >> ~/.bashrc

cd $NETWORK_VOLUME/ComfyUI/custom_nodes

if [ ! -d "ComfyUI-WanVideoWrapper" ]; then
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git
else
    cd ComfyUI-WanVideoWrapper
    git pull
fi

# Install dependencies
pip install --no-cache-dir -r $NETWORK_VOLUME/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper/requirements.txt
# Start ComfyUI
echo "Starting ComfyUI"
if [ "$USE_SAGE_ATTENTION" = "false" ]; then
    python3 "$NETWORK_VOLUME/ComfyUI/main.py" --listen
else
    python3 "$NETWORK_VOLUME/ComfyUI/main.py" --listen --use-sage-attention
    if [ $? -ne 0 ]; then
        echo "ComfyUI failed with --use-sage-attention. Retrying without it..."
        python3 "$NETWORK_VOLUME/ComfyUI/main.py" --listen
    fi
fi
