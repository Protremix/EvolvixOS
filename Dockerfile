# EvolvixOS — Dockerfile
# 100% local AI agent in a container. Zero tokens.
FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ffmpeg portaudio19-dev python3-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# App directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create dirs
RUN mkdir -p data/projects logs output/{code,videos,audio,images,research} data/github_cache

# Expose ports
EXPOSE 5000 5001

# Start script: Ollama + models + EvolvixOS
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
