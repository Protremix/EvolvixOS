#!/bin/bash
# EvolvixOS — Docker Entrypoint
# Starts Ollama, pulls models, then launches EvolvixOS

set -e

echo "🧬 EvolvixOS Docker — Starting..."

# Start Ollama in background
ollama serve &
sleep 3

# Pull models if not present
echo "📦 Checking models..."
ollama list 2>/dev/null | grep -q "deepseek-r1" || ollama pull deepseek-r1:7b 2>/dev/null || echo "⚠ deepseek-r1 pull failed (will retry on first use)"
ollama list 2>/dev/null | grep -q "qwen2.5-coder" || ollama pull qwen2.5-coder:7b 2>/dev/null || echo "⚠ qwen2.5-coder pull failed"
ollama list 2>/dev/null | grep -q "llama3.2" || ollama pull llama3.2:3b 2>/dev/null || echo "⚠ llama3.2 pull failed"

echo "✅ Models ready"

# Start EvolvixOS
if [ "$1" = "--api" ]; then
    echo "🧬 Starting API server on port 5001..."
    exec python main.py --api
elif [ "$1" = "--web" ]; then
    echo "🌐 Starting Web UI on port 5000..."
    exec python main.py --web
elif [ "$1" = "--web" ] && [ "$2" = "--api" ]; then
    echo "🧬 Starting Web UI + API..."
    exec python main.py --web --api
elif [ "$1" = "--discover" ]; then
    echo "🔍 Discovering GitHub skills..."
    exec python discover_skills.py auto
else
    echo "🧬 Starting interactive mode..."
    exec python main.py "$@"
fi
