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
        ipykernel jupyterlab_code_formatter

# ------------------------------------------------------------
# ComfyUI install
# ------------------------------------------------------------
RUN --mount=type=cache,target=/root/.cache/pip \
    /usr/bin/yes | comfy --workspace /ComfyUI install

FROM base AS final
# Make sure to use the virtual environment here too
ENV PATH="/opt/venv/bin:$PATH"

# Accept build argument for model type
ARG MODEL_TYPE=""

RUN pip install opencv-python

RUN for repo in \
    https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git \
    https://github.com/kijai/ComfyUI-KJNodes.git \
    https://github.com/rgthree/rgthree-comfy.git \
    https://github.com/JPS-GER/ComfyUI_JPS-Nodes.git \
    https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes.git \
    https://github.com/Jordach/comfy-plasma.git \
    https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git \
    https://github.com/bash-j/mikey_nodes.git \
    https://github.com/ltdrdata/ComfyUI-Impact-Pack.git \
    https://github.com/Fannovel16/comfyui_controlnet_aux.git \
    https://github.com/yolain/ComfyUI-Easy-Use.git \
    https://github.com/kijai/ComfyUI-Florence2.git \
    https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper.git \
    https://github.com/WASasquatch/was-node-suite-comfyui.git \
    https://github.com/theUpsider/ComfyUI-Logic.git \
    https://github.com/cubiq/ComfyUI_essentials.git \
    https://github.com/chrisgoringe/cg-image-picker.git \
    https://github.com/chflame163/ComfyUI_LayerStyle.git \
    https://github.com/chrisgoringe/cg-use-everywhere.git \
    https://github.com/welltop-cn/ComfyUI-TeaCache.git \
    https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git \
    https://github.com/Jonseed/ComfyUI-Detail-Daemon.git \
    https://github.com/kijai/ComfyUI-WanVideoWrapper.git \
    https://github.com/chflame163/ComfyUI_LayerStyle_Advance.git \
    https://github.com/BadCafeCode/masquerade-nodes-comfyui.git \
    https://github.com/1038lab/ComfyUI-RMBG.git \
    https://github.com/M1kep/ComfyLiterals.git; \
    do \
        cd /ComfyUI/custom_nodes; \
        repo_dir=$(basename "$repo" .git); \
        if [ "$repo" = "https://github.com/ssitu/ComfyUI_UltimateSDUpscale.git" ]; then \
            git clone --recursive "$repo"; \
        else \
            git clone "$repo"; \
        fi; \
        if [ -f "/ComfyUI/custom_nodes/$repo_dir/requirements.txt" ]; then \
            pip install -r "/ComfyUI/custom_nodes/$repo_dir/requirements.txt"; \
        fi; \
        if [ -f "/ComfyUI/custom_nodes/$repo_dir/install.py" ]; then \
            python "/ComfyUI/custom_nodes/$repo_dir/install.py"; \
        fi; \
    done

# Install Python dependencies
COPY builder/requirements.txt /requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

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

# Set the handler as the command
CMD python -u handler.py