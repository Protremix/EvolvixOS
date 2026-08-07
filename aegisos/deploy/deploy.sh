#!/bin/bash
set -euo pipefail

SERVER_IP=${1:-}
REMOTE_USER=${REMOTE_USER:-root}
DEPLOY_DIR=/opt/evolvixos

echo "=== EvolvixOS Production Deployment ==="

# Build frontend
echo "[1/5] Building frontend..."
cd frontend && npm run build && cd ..

# Run tests
echo "[2/5] Running tests..."
cd backend && python -m pytest --tb=line -q && cd ..

# Build Docker images
echo "[3/5] Building Docker images..."
docker compose -f docker-compose.prod.yml build

if [ -n "$SERVER_IP" ]; then
    echo "[4/5] Deploying to ${SERVER_IP}..."
    rsync -avz --exclude='node_modules' --exclude='.git' --exclude='__pycache__' \
        -e "ssh" ./ ${REMOTE_USER}@${SERVER_IP}:${DEPLOY_DIR}/
    ssh ${REMOTE_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker compose -f docker-compose.prod.yml up -d"
    ssh ${REMOTE_USER}@${SERVER_IP} "cd ${DEPLOY_DIR} && docker exec evolvixos-api python -m alembic upgrade head"
    echo "[5/5] Deployment complete: https://evolvixos.verdischain.com"
else
    echo "[4/5] Starting locally..."
    docker compose -f docker-compose.prod.yml up -d
    echo "[5/5] Local deployment complete: http://localhost:8000"
fi
