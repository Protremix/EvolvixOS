# EvolvixOS Platform Dockerfile
FROM python:3.12-slim

LABEL maintainer="EvolvixOS"
LABEL description="Self-hostable AI engineering platform"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY platform/ ./platform/
COPY auth/ ./auth/
COPY models/ ./models/
COPY web/ ./web/
COPY dashboard-dist/ ./dashboard-dist/

# Env defaults
ENV JWT_SECRET=change-me-in-production \
    EVOLVIX_PRIVACY_MODE=HYBRID \
    PORT=8080

EXPOSE 8080 5000 5010

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start platform
CMD ["python3", "platform/main.py"]
