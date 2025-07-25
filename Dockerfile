# Use multi-stage build with caching optimizations
FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu24.04 AS base

# Consolidated environment variables
ENV DEBIAN_FRONTEND=noninteractive \
   PIP_PREFER_BINARY=1 \
   PYTHONUNBUFFERED=1 \
   CMAKE_BUILD_PARALLEL_LEVEL=8

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.12 python3.12-venv python3.12-dev \
        python3-pip \
        curl ffmpeg ninja-build git aria2 git-lfs wget vim \
        libgl1 libglib2.0-0 build-essential gcc && \
    \
    # make Python3.12 the default python & pip
    ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    \
    python3.12 -m venv /opt/venv && \
    \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Use the virtual environment
ENV PATH="/opt/venv/bin:$PATH"

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.7.0 torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/cu128 || \
    pip install torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/cu121

# Core Python tooling
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install packaging setuptools wheel

# Runtime libraries
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install pyyaml gdown triton comfy-cli jupyterlab jupyterlab-lsp \
        jupyter-server jupyter-server-terminals \
        ipykernel jupyterlab_code_formatter flask requests

# ------------------------------------------------------------
# ComfyUI install
# ------------------------------------------------------------
RUN --mount=type=cache,target=/root/.cache/pip \
    # Clone ComfyUI directly for better control
    git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI && \
    cd /ComfyUI && \
    pip install -r requirements.txt && \
    # Install additional dependencies
    pip install websocket-client

FROM base AS final
# Make sure to use the virtual environment here too
ENV PATH="/opt/venv/bin:$PATH"

# Accept build argument for model type
ARG MODEL_TYPE=""

RUN pip install opencv-python

# Install essential custom nodes for Wan video generation
RUN --mount=type=cache,target=/root/.cache/pip \
    cd /ComfyUI/custom_nodes && \
    # Core video processing nodes
    git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git && \
    git clone https://github.com/kijai/ComfyUI-KJNodes.git && \
    git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git && \
    git clone https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git && \
    # UI and workflow nodes
    git clone https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git && \
    git clone https://github.com/rgthree/rgthree-comfy.git && \
    git clone https://github.com/cubiq/ComfyUI_essentials.git && \
    git clone https://github.com/chrisgoringe/cg-use-everywhere.git && \
    # Upscaling nodes
    git clone --recursive https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git && \
    # Install requirements with no-deps to avoid PyTorch conflicts
    for dir in */; do \
        if [ -f "$dir/requirements.txt" ]; then \
            echo "Installing requirements for $dir"; \
            pip install --no-deps -r "$dir/requirements.txt" || echo "Failed to install some deps for $dir, continuing..."; \
        fi; \
    done

# Install Python dependencies
COPY builder/requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt && \
    # Clean up to save space
    pip cache purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy source files  
ADD src .

# Copy additional files
COPY src/start_script.sh /start_script.sh
RUN chmod +x /start_script.sh
COPY 4xLSDIR.pth /4xLSDIR.pth

# Set environment variables for Wan model downloads
ENV download_480p_native_models=true \
    download_720p_native_models=true \
    download_vace=true \
    change_preview_method=true \
    enable_optimizations=true

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ -n "$RUNPOD_ENDPOINT_ID" ]; then\n\
    echo "🚀 Running in serverless mode"\n\
    python -u handler.py\n\
else\n\
    echo "🖥️ Running in pod mode"\n\
    /start_script.sh\n\
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]