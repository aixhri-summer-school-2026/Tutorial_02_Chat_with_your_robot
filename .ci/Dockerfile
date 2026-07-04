FROM ubuntu:24.04

# --- SYSTEM SETUP & DEPENDENCIES (ROOT) ---
ENV DEBIAN_FRONTEND=noninteractive
ARG UID=1000
ARG GID=1000

# Group all apt-get installs together to prevent layer bloat and permission errors
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git git-lfs ca-certificates build-essential cmake pkg-config \
    libcamera-ipa libcamera-tools v4l-utils \
    libgstreamer-plugins-bad1.0-dev libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev libglib2.0-dev libssl-dev libgirepository1.0-dev \
    libcairo2-dev libportaudio2 libnice10 gstreamer1.0-tools \
    gstreamer1.0-libcamera gstreamer1.0-plugins-good gstreamer1.0-alsa \
    gstreamer1.0-plugins-bad gstreamer1.0-nice gstreamer1.0-pulseaudio \
    pipewire alsa-utils python3-gi python3-gi-cairo libsndfile1 \
    libopenblas-dev nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

RUN git lfs install

# --- USER & PERMISSIONS (ROOT) ---
RUN groupadd -g ${GID} reachy && \
    useradd -m -u ${UID} -g reachy -s /bin/bash reachy && \
    usermod -aG dialout,audio reachy && \
    groupadd -f render && usermod -aG render reachy

# Create directories and assign ownership before switching users
RUN mkdir -p /opt/reachy_mini_env /opt/gst-plugins-rs /app && \
    chown -R reachy:reachy /opt/reachy_mini_env /opt/gst-plugins-rs /app

# --- SWITCH TO NON-ROOT USER ---
USER reachy
WORKDIR /app

# --- RUST & GSTREAMER WEBRTC PLUGIN ---
ENV PATH="/home/reachy/.cargo/bin:${PATH}"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

WORKDIR /tmp
RUN git clone https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs.git && \
    cd gst-plugins-rs && git checkout 0.14.5 && \
    cargo install cargo-c && \
    cargo cinstall -p gst-plugin-webrtc --prefix=/opt/gst-plugins-rs --release && \
    rm -rf /tmp/gst-plugins-rs
WORKDIR /app

ENV GST_PLUGIN_PATH="/opt/gst-plugins-rs/lib/x86_64-linux-gnu:${GST_PLUGIN_PATH}"

# --- PYTHON & UV ENVIRONMENT ---
ENV PATH="/home/reachy/.local/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV VIRTUAL_ENV=/opt/reachy_mini_env
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN uv python install 3.12 --default && \
    uv venv $VIRTUAL_ENV --python 3.12

# --- PYTHON PACKAGES ---
# Combined all uv installs into a single layer
RUN uv pip install --python $VIRTUAL_ENV \
    "reachy-mini" "opencv-python" \
    "jupyter" "ipywidgets" "notebook" "jupyterlab" "jupyterlab_widgets" \
    torch torchvision torchcodec accelerate "numpy>=2.0.0" "scipy>=1.14.0" \
    soundfile huggingface_hub pocket-tts transformers Pillow \
    "nvidia-cublas-cu12" "nvidia-cudnn-cu12==9.*" \
    "silero-vad" "faster-whisper"

# Llama-cpp-python with dynamic CMake arguments
ARG CMAKE_ARGS
ENV CMAKE_ARGS=${CMAKE_ARGS}
RUN uv pip install --python $VIRTUAL_ENV llama-cpp-python --no-binary llama-cpp-python

# --- PRE-CACHE MODELS ---
RUN python -c "from pocket_tts import TTSModel; TTSModel.load_model(language='english')" && \
    python -c "from silero_vad import load_silero_vad; load_silero_vad()" && \
    python -c "from faster_whisper import download_model; download_model('tiny.en')"

COPY --chown=reachy:reachy ./models /app/models

# --- CONFIGURATION & PATCHES ---
ENV LD_LIBRARY_PATH="/opt/reachy_mini_env/lib/python3.12/site-packages/nvidia/cublas/lib:/opt/reachy_mini_env/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH}"
ENV TERM=xterm-256color

RUN echo "source /opt/reachy_mini_env/bin/activate" >> /home/reachy/.bashrc && \
    sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /home/reachy/.bashrc && \
    echo "alias ls='ls --color=auto'" >> /home/reachy/.bashrc && \
    echo "alias grep='grep --color=auto'" >> /home/reachy/.bashrc

# Jupyter Dark Mode
RUN mkdir -p /opt/reachy_mini_env/share/jupyter/lab/settings && \
    echo '{"@jupyterlab/apputils-extension:themes": {"theme": "JupyterLab Dark"}}' \
    > /opt/reachy_mini_env/share/jupyter/lab/settings/overrides.json

# Camera patch
RUN sed -i 's/return find_video_device(devices)/return "\/dev\/reachy_camera", _make_camera_specs("Reachy")/' \
    /opt/reachy_mini_env/lib/python3.12/site-packages/reachy_mini/media/device_detection.py

CMD ["reachy-mini-daemon"]