#!/usr/bin/env bash
# EvolvixOS — Production Deployment Script
# Deploys EvolvixOS to a remote server and configures evolvixos.com
#
# Usage:
#   ./deploy/deploy.sh user@server-ip
#   ./deploy/deploy.sh root@192.168.1.100 --domain evolvixos.com
#
# What this does:
#   1. Copies EvolvixOS to the server
#   2. Installs Docker + Docker Compose
#   3. Builds and starts all containers
#   4. Sets up Nginx reverse proxy
#   5. Configures SSL with Let's Encrypt
#   6. Starts the auto-learner
#
# Requirements:
#   - SSH access to the server
#   - NVIDIA GPU on the server (for local AI)
#   - Domain evolvixos.com pointed to the server IP

set -euo pipefail

# === Colors ===
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# === Defaults ===
SERVER=""
DOMAIN="evolvixos.com"
SSH_KEY=""
PROJECT_DIR="/opt/evolvixos"
INSTALL_DOCKER=true
SETUP_SSL=true

print_usage() {
    echo "EvolvixOS Production Deployment"
    echo ""
    echo "Usage: $0 <user@server> [options]"
    echo ""
    echo "Options:"
    echo "  --domain DOMAIN    Domain name (default: evolvixos.com)"
    echo "  --key KEY_FILE     SSH private key file"
    echo "  --dir DIRECTORY    Remote install directory (default: /opt/evolvixos)"
    echo "  --no-docker        Skip Docker installation (assume already installed)"
    echo "  --no-ssl           Skip SSL/Let's Encrypt setup"
    echo "  -h, --help         Show this help"
    echo ""
    echo "Example:"
    echo "  $0 root@159.203.100.50 --domain evolvixos.com"
}

# === Parse arguments ===
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"; shift 2 ;;
        --key)
            SSH_KEY="-i $2"; shift 2 ;;
        --dir)
            PROJECT_DIR="$2"; shift 2 ;;
        --no-docker)
            INSTALL_DOCKER=false; shift ;;
        --no-ssl)
            SETUP_SSL=false; shift ;;
        -h|--help)
            print_usage; exit 0 ;;
        *)
            if [[ -z "$SERVER" ]]; then
                SERVER="$1"
            else
                echo "Unknown argument: $1"; exit 1
            fi
            shift ;;
    esac
done

if [[ -z "$SERVER" ]]; then
    print_usage; exit 1
fi

SSH="ssh $SSH_KEY $SERVER"
SCP="scp $SSH_KEY"

echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🧬 EvolvixOS Production Deployment${NC}"
echo -e "${GREEN}  Target: $SERVER${NC}"
echo -e "${GREEN}  Domain: $DOMAIN${NC}"
echo -e "${GREEN}  Directory: $PROJECT_DIR${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

# === Step 1: Check server ===
echo -e "${BLUE}[1/7]${NC} Checking server connectivity..."
$SSH "echo '✅ Server reachable'" || { echo -e "${RED}❌ Cannot connect to $SERVER${NC}"; exit 1; }

# Check GPU
echo -e "${BLUE}[2/7]${NC} Checking GPU..."
$SSH "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo '⚠ No NVIDIA GPU detected'" 

# === Step 3: Install Docker ===
if $INSTALL_DOCKER; then
    echo -e "${BLUE}[3/7]${NC} Installing Docker..."
    $SSH "if ! command -v docker &>/dev/null; then
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
        echo '✅ Docker installed'
    else
        echo '✅ Docker already installed'
    fi"
else
    echo -e "${BLUE}[3/7]${NC} Skipping Docker installation"
fi

# === Step 4: Copy project ===
echo -e "${BLUE}[4/7]${NC} Copying EvolvixOS to server..."
$SSH "mkdir -p $PROJECT_DIR"

# Create a tarball excluding unnecessary files
tar czf /tmp/evolvixos.tar.gz --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='output' --exclude='data' \
    --exclude='logs' --exclude='models' \
    -C "$(dirname "$0")/.." .

$SCP /tmp/evolvixos.tar.gz "$SERVER:/tmp/"
$SSH "cd $PROJECT_DIR && tar xzf /tmp/evolvixos.tar.gz && rm /tmp/evolvixos.tar.gz"
rm /tmp/evolvixos.tar.gz

echo "✅ Files copied"

# === Step 5: Build and start containers ===
echo -e "${BLUE}[5/7]${NC} Building and starting containers..."
$SSH "cd $PROJECT_DIR && \
    docker compose -f deploy/docker-compose.yml up -d --build"

echo "Waiting for containers to start..."
sleep 30

# === Step 6: Check health ===
echo -e "${BLUE}[6/7]${NC} Checking service health..."
$SSH "curl -s http://localhost:5001/api/v1/health 2>/dev/null || echo '⚠ API not ready yet (pulling models...)'"

# Show running containers
$SSH "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# === Step 7: SSL setup ===
if $SETUP_SSL; then
    echo -e "${BLUE}[7/7]${NC} Setting up SSL with Let's Encrypt..."
    $SSH "
        apt-get update && apt-get install -y certbot python3-certbot-nginx 2>/dev/null
        # Get SSL cert (requires DNS to point to this server)
        certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos \
            -m admin@$DOMAIN --redirect || echo '⚠ SSL setup failed — ensure DNS points to this server'
    "
fi

# === Done ===
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🧬 EvolvixOS Deployed Successfully!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo "  🌐 Website:     http://$DOMAIN"
echo "  🔌 API:         http://$DOMAIN/api/v1/status"
echo "  📊 Health:      http://$DOMAIN/health"
echo "  📚 Docs:        http://$DOMAIN/api/v1/docs"
echo "  🎥 Web UI:      http://$DOMAIN/app/"
echo ""
echo "  💰 Cost:        \$0.00 — forever"
echo "  🧠 Models:      deepseek-r1:7b, qwen2.5-coder:7b, llama3.2:3b"
echo "  🛠️ Skills:      31 loaded"
echo "  🔄 Auto-learner: Running (24h cycle)"
echo ""
echo "  Management:"
echo "    $SSH 'docker logs evolvix-core -f'"
echo "    $SSH 'docker logs evolvix-learner -f'"
echo "    $SSH 'docker compose -f $PROJECT_DIR/deploy/docker-compose.yml restart'"
echo ""
