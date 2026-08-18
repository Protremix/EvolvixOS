# EvolvixOS v9.2 Documentation

> **The open-source, self-hosted AI engineering platform.**
> 44 tools · 81 models · 35,277 APIs · Triple-brain routing · Zero paid tokens for core logic

## Quick Links

- 🌐 **Live Platform**: [evolvixos.com](https://evolvixos.com)
- 📦 **GitHub**: [github.com/Protremix/EvolvixOS](https://github.com/Protremix/EvolvixOS)
- 🎨 **Studio Dashboard**: [evolvixos.com/studio](https://evolvixos.com/studio)
- 📖 **Model Browser**: [evolvixos.com/models](https://evolvixos.com/models)
- 🔍 **API Directory**: [evolvixos.com/apis](https://evolvixos.com/apis)
- 🎓 **Learning Hub**: [evolvixos.com/learn](https://evolvixos.com/learn)
- 🔑 **Developer Portal**: [evolvixos.com/developer](https://evolvixos.com/developer)

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Mr James v9.2 — Triple-Brain Routing](#mr-james-v92--triple-brain-routing)
- [44 Tools](#44-tools)
- [Integrations](#integrations)
  - [Tencent Cloud SDK](#1-tencent-cloud-sdk)
  - [Octop — AI Assistant](#2-octop--ai-assistant)
  - [CubeSandbox — MicroVM](#3-cubesandbox--microvm-execution)
  - [TIMSDK — Messaging](#4-timsdk--real-time-messaging)
  - [TencentDB Agent Memory](#5-tencentdb-agent-memory)
  - [Google Gemini 3.6 Flash](#6-google-gemini-36-flash)
  - [Groq Integration](#7-groq-integration)
- [Discovery Engine](#discovery-engine)
- [API Reference](#api-reference)
- [Security](#security)
- [Configuration](#configuration)
- [Quick Start](#quick-start)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      EvolvixOS v9.2 Platform                     │
├──────────────────┬──────────────────┬───────────────────────────┤
│   Mr James v9.2   │    Model API     │      Auth API             │
│   44 tools        │    :5010         │      :5000                │
│   Triple-brain    │    81 models     │      JWT + OTP            │
│   routing         │    Groq+Gemini   │      SHA-256 API keys     │
│                   │    +Kimi+Ollama  │      Rate limiting        │
├──────────────────┼──────────────────┼───────────────────────────┤
│  Discovery Engine │  Dashboard       │   Developer Portal        │
│  Hourly GitHub    │  evolvixos.com   │   /developer              │
│  4 repos synced   │  /studio         │   API key management      │
│  35K APIs indexed │  /models         │   API documentation       │
├──────────────────┴──────────────────┴───────────────────────────┤
│                     Backend Services                             │
├───────────────┬──────────────┬──────────────┬───────────────────┤
│ TencentDB     │ CubeSandbox  │  TIMSDK      │  Octop            │
│ Agent Memory   │ MicroVM      │  Chat SDK    │  217 subagents    │
│ 3 containers   │ (Docker)     │  1K MAU     │  16 MBTI profiles │
├───────────────┴──────────────┴──────────────┴───────────────────┤
│                   Tencent Cloud SDK                              │
│   Go binary (tccli) + Python SDK (12 services)                   │
├──────────────────────────────────────────────────────────────────┤
│              Infrastructure (16 systemd services)                 │
│  Nginx HTTPS · Let's Encrypt SSL · Ollama · Docker              │
│  Server: Hetzner Cloud (16 vCPU, 30GB RAM, 600GB disk)          │
└──────────────────────────────────────────────────────────────────┘
```

## Mr James v9.2 — Triple-Brain Routing

Mr James uses intelligent intent-based routing to select the best AI engine for each task.

| Engine | Model | Speed | Context | Primary Use |
|--------|-------|-------|---------|-------------|
| Groq | gpt-oss-120b | 467 tok/s | 128K | Tool-use precision, agentic execution |
| Google Gemini | 3.6 Flash | Fast | 1M | Vision, multimodal, TTS, large context |
| Kimi | moonshot-v1-32k | Medium | 32K | Complex reasoning fallback |
| Ollama | qwen2.5:14b/7b/3b | CPU | 32K | Local, offline, zero-cost fallback |

## 44 Tools

### File Operations (6)
- `file_read` — Read file contents
- `file_write` — Write/create files
- `file_edit` — Edit existing files
- `file_list` — List directory contents
- `file_delete` — Delete files
- `code_analyze` — Analyze code with AI

### Code Execution (3)
- `python_exec` — Execute Python code
- `bash_exec` — Execute shell commands (shlex.split, shell=False)
- `sandbox_exec` — CubeSandbox MicroVM isolated execution

### AI/LLM (4)
- `call_free_llm` — Delegate to 442+ free LLM APIs across 31 providers
- `gemini_vision` — Image analysis, OCR, chart reading, UI screenshots
- `gemini_tts` — Text-to-speech via Gemini
- `file_upload` — Upload with Gemini Vision analysis (50MB max)

### Smart API (3)
- `api_auto_route` — Semantic API discovery across 35,277 resources
- `smart_api_call` — HTTP API execution
- `http_request` — Generic HTTP requests

### Tencent Cloud (1)
- `tencent_cloud` — 12 Python services + 7 Go binary services (CVM, CDB, VPC, SSL, DNSPod, CDN, Billing, CAM, Hunyuan, AIArt)

### TIMSDK Chat (4)
- `tim_send_message` — Direct messaging
- `tim_create_group` — Group creation
- `tim_send_group_message` — Group messaging
- `tim_import_user` — User import

### Team Memory (2)
- `team_memory_search` — TencentDB full-text search
- `team_memory_save` — TencentDB memory persistence

### Agent Library (2)
- `search_subagents` — Search 217 agent templates across 16 categories
- `set_persona` — Switch between 16 MBTI personality profiles

### System (3)
- `get_system_info` — Server status and specs
- `manage_services` — Start/stop systemd services
- `get_service_logs` — View service logs

## Integrations

### 1. Tencent Cloud SDK
- **Go binary** (`tccli`, 9.3MB): 7 services, 14 actions — high-performance CLI
- **Python SDK**: 12 services — comprehensive API coverage
- **Services**: CVM (servers), CDB (MySQL), VPC (networking), SSL (certificates), DNSPod (DNS), CDN, Billing (costs), CAM (users), Hunyuan (Tencent LLM), AIArt (image generation)
- **Config**: Requires `TENCENTCLOUD_SECRET_ID` and `TENCENTCLOUD_SECRET_KEY`

### 2. Octop — AI Assistant
- **217 subagent templates** across 16 categories:
  - Engineering (33), Specialized (53), Marketing (36), Security (10)
  - Product (15), Operations (12), Design (8), Data (11), Research (9), Finance (7)
- **16 MBTI personality profiles** with behavior mappings:
  - Answer style, casual chat, conflict handling, creativity, emotion, planning
- **10 expert agent templates**:
  - General Assistant, Ops Engineer, News & Trend, WeChat Ops, CVM AI Doctor, Stock Assistant, Office Automation, Parenting Companion, CVM Cluster Doctor, Default
- **SSRF Guard** (CWE-918 mitigation) ported from Octop

### 3. CubeSandbox — MicroVM Execution
- Isolated code execution sandbox for AI agents
- **Docker fallback mode** (KVM not available on Hetzner Cloud)
- Pre-installed: numpy, pandas, scikit-learn, matplotlib
- Full MicroVM mode on CCX dedicated CPU servers (set `SANDBOX_ENABLED=True`)

### 4. TIMSDK — Real-Time Messaging
- Tencent IM SDK for chat integration
- 1,000 MAU free tier
- Server-side REST API + Web UIKit
- **Config**: Requires `TIM_SDK_APP_ID` and `TIM_SECRET_KEY`

### 5. TencentDB Agent Memory
- 3 Docker containers:
  - `tdai-memory-core` (:8420) — Core memory service
  - `tdai-memory-hub` (:8125) — Memory hub
  - `tdai-proxy` (:8096) — Proxy (Groq-powered)
- Team memory with full-text search
- Panel at `memory.evolvixos.com`

### 6. Google Gemini 3.6 Flash
- 37 models available (vision, multimodal, TTS)
- 1M token context window
- `gemini_vision` tool: image analysis, OCR, chart reading, UI screenshots
- `gemini_tts` tool: text-to-speech
- File upload analysis: images, PDFs, documents

### 7. Groq Integration
- gpt-oss-120b at 467 tok/s
- Primary execution engine for agentic tool-use
- Auto-fallback to Ollama when overloaded

## Discovery Engine

Hourly GitHub scans across 4 repositories:

| Repository | Content | Count |
|------------|---------|-------|
| OpenClaw API Directory | APIs across 18 categories | 25,822 |
| API Mega List | Public API registries | 7,000+ |
| AI Agent Tools | Tools for AI agent development | 84 |
| Free LLM APIs | Models across 31 providers | 442+ |
| **Total** | **Searchable APIs/tools** | **35,277** |

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | — | System health check |
| `/api/agent/stream` | POST | JWT/API | Streaming agent response |
| `/api/agent` | POST | JWT/API | Non-streaming agent response |
| `/api/models` | GET | — | List all registered models |
| `/api/upload` | POST | JWT | File upload (50MB max) |
| `/api/docs` | GET | — | API documentation |
| `/auth/register` | POST | — | User registration (OTP) |
| `/auth/login` | POST | — | User login (OTP) |
| `/auth/api-keys/generate` | POST | JWT | Generate API key |
| `/auth/api-keys/list` | GET | JWT | List API keys |
| `/auth/api-keys/revoke` | DELETE | JWT | Revoke API key |
| `/auth/api-keys/usage` | GET | JWT | API key usage stats |

## Security

- **JWT authentication** with OTP verification
- **Per-user API keys** (SHA-256 hashed, `evx_` prefix)
- **Rate limiting**: 30/min per IP, 100/min per API key
- **SSRF guard** (CWE-918 mitigation)
- **Shell injection protection** (shlex.split, shell=False)
- **21 error handling blocks** patched

## Configuration

```bash
# Required for core
export JWT_SECRET="your-secret"

# Optional: External AI brains
export GROQ_API_KEY="your-groq-key"
export GEMINI_API_KEY="your-gemini-key"
export KIMI_API_KEY="your-kimi-key"

# Optional: Tencent Cloud
export TENCENTCLOUD_SECRET_ID="your-id"
export TENCENTCLOUD_SECRET_KEY="your-key"

# Optional: Tencent IM
export TIM_SDK_APP_ID="your-app-id"
export TIM_SECRET_KEY="your-secret"
```

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS

# Deploy (requires Ubuntu 22.04+)
chmod +x gpu_deploy.sh
./gpu_deploy.sh

# Or manual setup
pip3 install -r requirements.txt
python3 models/model_api.py &  # Model API on :5010
python3 auth/auth_api.py &      # Auth API on :5000
python3 dashboard/server.py &   # Dashboard on :8080
```

## Server Infrastructure

| Component | Detail |
|-----------|--------|
| Provider | Hetzner Cloud (Nuremberg) |
| Specs | 16 vCPU, 30GB RAM, 600GB disk |
| OS | Ubuntu 22.04 |
| Python | 3.14 |
| Go | 1.23.4 |
| Services | 16 systemd services (all stable) |
| SSL | Let's Encrypt (valid until Nov 2026) |
| Domain | evolvixos.com → 2.28.52.223 |
| Containers | 3 (TencentDB Memory) + 1 (CubeSandbox) |

## License

MIT
