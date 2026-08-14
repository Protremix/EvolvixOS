#!/bin/bash
# EvolvixOS v0.2 — Setup Script
# Installs everything for 100% local AI: API, project learning, voice, video, research, coding.
# Zero tokens, zero external API calls.

set -e

echo "🧬 EvolvixOS v0.2 Setup"
echo "======================="
echo "100% local • zero tokens • open source"
echo "Features: API, project learning, voice, video, research, coding, deploy"
echo ""

# === 1. Ollama ===
echo "📦 Step 1/6: Installing Ollama (local LLM, zero tokens)..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh
    echo "✅ Ollama installed"
else
    echo "✅ Ollama already installed"
fi

# === 2. Download models ===
echo ""
echo "📦 Step 2/6: Downloading AI models (free, one-time)..."
echo "  ↓ deepseek-r1:7b (reasoning brain)..."
ollama pull deepseek-r1:7b 2>/dev/null || echo "  ⚠ Retry on first run"
echo "  ↓ qwen2.5-coder:7b (coding + project understanding)..."
ollama pull qwen2.5-coder:7b 2>/dev/null || echo "  ⚠ Retry on first run"
echo "  ↓ llama3.2:3b (fast tasks)..."
ollama pull llama3.2:3b 2>/dev/null || echo "  ⚠ Retry on first run"
echo "✅ Models downloaded"

# === 3. Python deps ===
echo ""
echo "📦 Step 3/6: Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# === 4. Whisper (for voice) ===
echo ""
echo "📦 Step 4/6: Installing Whisper (local speech-to-text)..."
pip install openai-whisper 2>/dev/null || echo "  ⚠ Whisper install failed (voice STT won't work)"
echo "✅ Whisper installed (first use downloads model)"

# === 5. SearXNG (for research) ===
echo ""
echo "📦 Step 5/6: Setting up SearXNG (local search engine)..."
if command -v docker &> /dev/null; then
    docker run -d --name evolvix-searxng -p 8888:8080 searxng/searxng 2>/dev/null || echo "  ⚠ SearXNG already running or Docker issue"
    echo "✅ SearXNG on http://localhost:8888"
else
    echo "  ⚠ No Docker. Agent will use DuckDuckGo HTML scraping."
fi

# === 6. Directories ===
echo ""
echo "📦 Step 6/6: Creating directories..."
mkdir -p data/projects logs output/{code,videos,audio,images,research}
echo "✅ Ready"

# === Done ===
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ EvolvixOS v0.2 setup complete!"
echo ""
echo "START MODES:"
echo "  Interactive:     python main.py"
echo "  Single task:      python main.py 'research quantum computing'"
echo "  Web UI:           python main.py --web"
echo "  API server:       python main.py --api"
echo "  Both web + API:   python main.py --web --api"
echo "  Voice mode:       python main.py --voice"
echo "  Analyze project:  python main.py --project /path/to/code"
echo ""
echo "API (for external projects):"
echo "  Base URL:  http://localhost:5001"
echo "  Endpoints: /api/v1/chat, /api/v1/voice, /api/v1/speak"
echo "             /api/v1/project/load, /api/v1/project/ask"
echo "             /api/v1/project/represent"
echo ""
echo "Client SDK: drop evolvix_client.py into any project"
echo ""
echo "100% local. Zero tokens. Your data never leaves your machine."
echo "═══════════════════════════════════════════════════════"
