# EvolvixOS Production Dockerfile
# Self-contained, zero-token, fully autonomous AI agent
# 
# Build: docker build -t evolvixos .
# Run:   docker run -d --gpus all -p 5001:5001 -p 5000:5000 evolvixos

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

LABEL maintainer="Protremix"
LABEL description="EvolvixOS — 100% Local AI Agent, Zero Tokens, 31 Skills"
LABEL version="0.4"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# === System dependencies ===
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-dev \
    git curl wget unzip \
    ffmpeg libsm6 libxext6 libxrender-dev \
    tesseract-ocr tesseract-ocr-eng \
    pandoc \
    portaudio19-dev \
    libsndfile1 \
    sqlite3 \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# === Install Ollama ===
RUN curl -fsSL https://ollama.com/install.sh | sh

# === Application ===
WORKDIR /opt/evolvixos

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# === Setup directories ===
RUN mkdir -p /opt/evolvixos/output \
             /opt/evolvixos/data \
             /opt/evolvixos/logs \
             /opt/evolvixos/models

# === Download Ollama models (will pull on first run) ===
# These are the default models — users can swap via config
ENV OLLAMA_HOST=0.0.0.0:11434
ENV EVOLVIX_ENV=production

# === Nginx config ===
COPY deploy/nginx.conf /etc/nginx/sites-available/evolvixos
RUN ln -sf /etc/nginx/sites-available/evolvixos /etc/nginx/sites-enabled/evolvixos \
    && rm -f /etc/nginx/sites-enabled/default

# === Supervisor config ===
COPY deploy/supervisord.conf /etc/supervisor/conf.d/evolvixos.conf

# === Health check ===
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:5001/api/v1/health || exit 1

# === Ports ===
EXPOSE 5001 5000 11434

# === Entry point ===
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/evolvixos.conf"]
