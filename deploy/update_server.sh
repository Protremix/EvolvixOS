#!/usr/bin/env bash
# EvolvixOS — Server Update Script
# Run this on the server to pull latest from GitHub and restart all services
#
# Usage:
#   ssh root@your-server-ip 'bash -s' < deploy/update_server.sh
#   OR copy to server and run: bash update_server.sh

set -e

EVOLVIX_DIR="/opt/evolvixos"
LOG_FILE="/var/log/evolvix-update.log"

echo "========================================" | tee "$LOG_FILE"
echo "  EvolvixOS Server Update" | tee -a "$LOG_FILE"
echo "  $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# Check if EvolvixOS directory exists
if [ ! -d "$EVOLVIX_DIR" ]; then
    echo "❌ EvolvixOS not found at $EVOLVIX_DIR" | tee -a "$LOG_FILE"
    echo "   Cloning from GitHub..." | tee -a "$LOG_FILE"
    git clone https://github.com/Protremix/EvolvixOS.git "$EVOLVIX_DIR"
fi

cd "$EVOLVIX_DIR"

# Pull latest from GitHub
echo "" | tee -a "$LOG_FILE"
echo "📥 Pulling latest from GitHub..." | tee -a "$LOG_FILE"
git fetch origin main 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/main 2>&1 | tee -a "$LOG_FILE"

# Show what we got
echo "" | tee -a "$LOG_FILE"
echo "📋 Latest commits:" | tee -a "$LOG_FILE"
git log --oneline -5 | tee -a "$LOG_FILE"

# Count skills
SKILL_COUNT=$(ls skills/ 2>/dev/null | wc -l)
echo "" | tee -a "$LOG_FILE"
echo "📊 Skills: $SKILL_COUNT" | tee -a "$LOG_FILE"

# Kill old processes
echo "" | tee -a "$LOG_FILE"
echo "🛑 Stopping old services..." | tee -a "$LOG_FILE"
pkill -f "api_server.py" 2>/dev/null || true
pkill -f "dashboard.py" 2>/dev/null || true
pkill -f "websocket_server.py" 2>/dev/null || true
sleep 2

# Start API server
echo "" | tee -a "$LOG_FILE"
echo "🚀 Starting API server (port 5001)..." | tee -a "$LOG_FILE"
cd "$EVOLVIX_DIR"
nohup python3 api_server.py > /var/log/evolvix-api.log 2>&1 &
sleep 3

# Check API
if curl -s http://localhost:5001/api/v1/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ API: {len(d.get(\"skills\",[]))} skills, models: {d.get(\"available_models\",[])}')" 2>/dev/null | tee -a "$LOG_FILE"; then
    echo "   API is running" | tee -a "$LOG_FILE"
else
    echo "⚠️  API failed to start — check /var/log/evolvix-api.log" | tee -a "$LOG_FILE"
    tail -20 /var/log/evolvix-api.log | tee -a "$LOG_FILE"
fi

# Start dashboard
echo "" | tee -a "$LOG_FILE"
echo "🖥️  Starting dashboard (port 5000)..." | tee -a "$LOG_FILE"
nohup python3 platform/dashboard.py > /var/log/evolvix-dashboard.log 2>&1 &
sleep 2

# Start websocket server
echo "🔌 Starting websocket server..." | tee -a "$LOG_FILE"
nohup python3 platform/websocket_server.py > /var/log/evolvix-ws.log 2>&1 &
sleep 2

# Final status
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "  ✅ UPDATE COMPLETE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Services:" | tee -a "$LOG_FILE"
echo "  API:       http://localhost:5001/api/v1/status" | tee -a "$LOG_FILE"
echo "  Dashboard:  http://localhost:5000" | tee -a "$LOG_FILE"
echo "  Web (nginx):http://localhost:80" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Logs:" | tee -a "$LOG_FILE"
echo "  API:       /var/log/evolvix-api.log" | tee -a "$LOG_FILE"
echo "  Dashboard: /var/log/evolvix-dashboard.log" | tee -a "$LOG_FILE"
echo "  Update:    /var/log/evolvix-update.log" | tee -a "$LOG_FILE"
