# 🧬 EvolvixOS v9.2

**The open-source, self-hosted AI engineering platform.**

100% local core. Zero paid tokens. 44 tools. 81 models. 35,277 searchable APIs. Triple-brain routing.

🌐 **[evolvixos.com](https://evolvixos.com)** · 📦 **[GitHub](https://github.com/Protremix/EvolvixOS)** · 📚 **[Docs](https://protremix.github.io/EvolvixOS/)**

---

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
│   CVM · CDB · VPC · SSL · DNSPod · CDN · Billing · CAM · Hunyuan │
├──────────────────────────────────────────────────────────────────┤
│              Infrastructure (16 systemd services)                 │
│  Nginx HTTPS · Let's Encrypt SSL · Ollama · Docker              │
│  Server: Hetzner Cloud (16 vCPU, 30GB RAM, 600GB disk)          │
└──────────────────────────────────────────────────────────────────┘
```

## Mr James v9.2 — Triple-Brain Routing

Mr James uses intelligent intent-based routing to select the best AI engine for each task:

| Engine | Model | Speed | Context | Primary Use |
|--------|-------|-------|---------|-------------|
| 🟢 **Groq** | gpt-oss-120b | 467 tok/s | 128K | Tool-use precision, agentic execution |
| 🔵 **Google Gemini** | 3.6 Flash | Fast | 1M | Vision, multimodal, TTS, large context |
| 🟡 **Kimi** | moonshot-v1-32k | Medium | 32K | Complex reasoning fallback |
| ⚪ **Ollama** | qwen2.5:14b/7b/3b | CPU | 32K | Local, offline, zero-cost fallback |

### 44 Tools

| Category | Count | Tools |
|----------|-------|-------|
| **File Operations** | 6 | file_read, file_write, file_edit, file_list, file_delete, code_analyze |
| **Code Execution** | 3 | python_exec, bash_exec, sandbox_exec (CubeSandbox MicroVM) |
| **AI/LLM** | 4 | call_free_llm, gemini_vision, gemini_tts, file_upload (with Gemini Vision) |
| **Smart API** | 3 | api_auto_route (35K APIs), smart_api_call, http_request |
| **Tencent Cloud** | 1 | tencent_cloud (CVM, CDB, VPC, SSL, DNSPod, CDN, Billing, CAM, Hunyuan, AIArt) |
| **TIMSDK Chat** | 4 | tim_send_message, tim_create_group, tim_send_group_message, tim_import_user |
| **Team Memory** | 2 | team_memory_search, team_memory_save (TencentDB Agent Memory) |
| **Agent Library** | 2 | search_subagents (217 templates), set_persona (16 MBTI types) |
| **System** | 3 | get_system_info, manage_services, get_service_logs |
| **Other** | 16 | web_search, image_gen, and more |

---

## Integrations (v9.2)

### 1. Tencent Cloud SDK
- **Go binary** (`tccli`, 9.3MB): 7 services, 14 actions — high-performance CLI
- **Python SDK**: 12 services — comprehensive API coverage
- **Services**: CVM (servers), CDB (MySQL), VPC (networking), SSL (certificates), DNSPod (DNS), CDN, Billing (costs), CAM (users), Hunyuan (Tencent LLM), AIArt (image generation)
- **Config**: Requires `TENCENTCLOUD_SECRET_ID` and `TENCENTCLOUD_SECRET_KEY`

### 2. Octop — Self-Hosted AI Assistant
- **217 subagent templates** across 16 categories:
  - Engineering (33), Specialized (53), Marketing (36), Security (10)
  - Product (15), Operations (12), Design (8), Data (11), Research (9), Finance (7), etc.
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
- 4 tools: send message, create group, send group message, import user
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

---

## Platform Features

### Frontend Pages
| Page | URL | Description |
|------|-----|-------------|
| Landing | `/` | Platform overview with architecture, capabilities |
| Studio | `/studio` | Zero-knowledge dashboard with smart bar |
| Models | `/models` | Visual model browser (81 models, 8 categories) |
| APIs | `/apis` | Searchable API directory (35K APIs, 33 categories) |
| Learn | `/learn` | Learning Hub (19-module full-stack course) |
| Developer | `/developer` | API key management and documentation |
| Auth | `/auth` | Login/signup with OTP |
| Memory | `memory.evolvixos.com` | Team memory panel |

### Model Registry
- **81 models** across 8 categories:
  - LLM Text (42), Vision (16), Audio (35), Video (61), Image (47), 3D (21), Coding (16), RAG/Agents (19)
- Sources: Ollama (13 local), GitHub Discovery (58), Built-in (10)
- Auto-rebuild via hourly cron

### Discovery Engine
Hourly GitHub scans across 4 repositories:
1. **OpenClaw API Directory** — 25,822 APIs across 18 categories
2. **API Mega List** — 7,000+ APIs
3. **AI Agent Tools** — 84 tools
4. **Free LLM APIs** — 442+ models across 31 providers

Total: **35,277 searchable APIs/tools**

### Security
- JWT authentication with OTP verification
- Per-user API keys (SHA-256 hashed, `evx_` prefix)
- Rate limiting: 30/min per IP, 100/min per API key
- SSRF guard (CWE-918 mitigation)
- Shell injection protection (shlex.split, shell=False)
- 21 error handling blocks patched

### API Endpoints
| Endpoint | Method | Auth | Description |
|----------|-------|------|-------------|
| `/api/health` | GET | — | System health check |
| `/api/agent/stream` | POST | JWT/API | Streaming agent response |
| `/api/agent` | POST | JWT/API | Non-streaming agent response |
| `/api/models` | GET | — | List all registered models |
| `/api/upload` | POST | JWT | File upload (50MB max, multipart) |
| `/api/docs` | GET | — | API documentation |
| `/auth/register` | POST | — | User registration (OTP) |
| `/auth/login` | POST | — | User login (OTP) |
| `/auth/api-keys/generate` | POST | JWT | Generate API key |
| `/auth/api-keys/list` | GET | JWT | List API keys |
| `/auth/api-keys/revoke` | DELETE | JWT | Revoke API key |
| `/auth/api-keys/usage` | GET | JWT | API key usage stats |

---

## Server Infrastructure

| Component | Detail |
|-----------|--------|
| **Provider** | Hetzner Cloud (Nuremberg) |
| **Specs** | 16 vCPU, 30GB RAM, 600GB disk |
| **OS** | Ubuntu 22.04 |
| **Python** | 3.14 |
| **Go** | 1.23.4 |
| **Services** | 16 systemd services (all stable) |
| **SSL** | Let's Encrypt (valid until Nov 2026) |
| **Domain** | evolvixos.com → 2.28.52.223 |
| **Containers** | 3 (TencentDB Memory) + 1 (CubeSandbox) |

## Stack
- **Backend**: Python 3.14, FastAPI-style HTTP, SQLite
- **AI**: Ollama (local), Groq (fast), Google Gemini (multimodal), Kimi (reasoning)
- **Cloud**: Tencent Cloud SDK (Python + Go binary)
- **Infrastructure**: systemd, Nginx, Let's Encrypt, Docker
- **Frontend**: Vanilla HTML/CSS/JS with dark theme (#0a0a0f + purple/pink neon)

---

## Quick Start

```bash
# Clone
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

## License
MIT
