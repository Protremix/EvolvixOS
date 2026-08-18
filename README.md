# EvolvixOS v9.2

**The open-source, self-hosted AI engineering platform.**

Fully local. Zero paid tokens for core logic. 44 tools. 81 models. 35,277 searchable APIs.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EvolvixOS Platform                     │
├─────────────┬──────────────┬──────────────┬──────────────┤
│  Mr James   │  Model API   │   Auth API   │  Discovery   │
│  v9.2       │  (5010)      │   (5000)    │  Engine       │
│  44 tools   │  81 models   │  JWT+OTP    │  Hourly sync  │
│  Triple AI  │  Groq+Kimi   │  API Keys   │  35K APIs     │
│  Brain      │  +Gemini     │  SHA-256    │               │
├─────────────┴──────────────┴──────────────┴──────────────┤
│                    Backend Services                       │
├──────────┬───────────┬──────────┬──────────┬─────────────┤
│ TencentDB│ CubeSand  │  TIMSDK  │ Octop    │ TencentCloud│
│ Memory   │ box       │  Chat    │ Subagents│ SDK (Go+Py) │
│ (3 Docker)│ (Docker) │ (1K MAU)│ 217 tmpl │ 12 services │
├──────────┴───────────┴──────────┴──────────┴─────────────┤
│              Infrastructure (systemd)                     │
│  Nginx HTTPS │ Ollama │ 16 services │ evolvixos.com       │
└─────────────────────────────────────────────────────────┘
```

## Mr James v9.2 — 44 Tools

### AI Brains (Triple Routing)
| Engine | Model | Speed | Use Case |
|--------|-------|-------|----------|
| Groq | gpt-oss-120b | 467 tok/s | Primary execution, tool-use precision |
| Google Gemini | 3.6 Flash | Fast | Vision, multimodal, TTS |
| Kimi | moonshot-v1-32k | Medium | Complex reasoning fallback |
| Ollama | qwen2.5:14b/7b/3b | CPU | Local, offline fallback |

### Tool Categories
| Category | Tools | Details |
|----------|-------|---------|
| **File Ops** | 6 | read, write, edit, list, delete, code_analyze |
| **Execution** | 3 | python_exec, bash_exec, sandbox_exec (CubeSandbox) |
| **AI/LLM** | 4 | call_free_llm, gemini_vision, gemini_tts, hunyuan chat |
| **API** | 3 | api_auto_route, smart_api_call, http_request |
| **Tencent Cloud** | 1 | tencent_cloud (CVM, CDB, VPC, SSL, DNSPod, CDN, Billing, CAM, Hunyuan, AIArt) |
| **TIMSDK Chat** | 4 | tim_send_message, tim_create_group, tim_send_group_message, tim_import_user |
| **Memory** | 2 | team_memory_search, team_memory_save (TencentDB) |
| **Agent Library** | 2 | search_subagents (217 templates), set_persona (16 MBTI) |
| **System** | 3 | get_system_info, manage_services, get_service_logs |
| **Other** | 16 | file_upload, web_search, and more |

### Tencent Cloud Integration (New in v9.2)
- **Tencent Cloud SDK**: 12 Python services + 7 Go binary services
- **Go binary** (`tccli`): 9.3MB, high-performance API calls
- **Services**: CVM (servers), CDB (databases), VPC (networking), SSL (certs), DNSPod (DNS), CDN, Billing, CAM (users), Hunyuan (LLM), AIArt (image gen)
- **Requires**: `TENCENTCLOUD_SECRET_ID` and `TENCENTCLOUD_SECRET_KEY` env vars

### Octop Integration (New in v9.2)
- **217 subagent templates** across 16 categories (engineering: 33, specialized: 53, marketing: 36, security: 10, etc.)
- **16 MBTI personality profiles** with behavior mappings for answer style, casual chat, conflict, creativity, emotion, planning
- **10 expert agent templates** (general-assistant, ops-engineer, news-trend, wechat-ops, cvm-ai-doctor, stock-assistant, office-automation, parenting-companion, cvm-cluster-doctor, default)
- **SSRF guard** (CWE-918 mitigation) ported from Octop

### CubeSandbox Integration (New in v9.2)
- MicroVM sandbox for isolated code execution
- Docker fallback mode (KVM not available on Hetzner Cloud)
- Pre-installed: numpy, pandas, scikit-learn, matplotlib
- Full MicroVM mode available on CCX dedicated CPU servers

### TencentDB Agent Memory (New in v9.2)
- 3 Docker containers: memory-core (8420), memory-hub (8125), proxy (8096)
- Team memory with full-text search
- Powered by Groq for memory processing
- Panel at memory.evolvixos.com

## Platform Stats
- **Models**: 81 registered (Ollama + Discovery + Built-in)
- **APIs/Tools**: 35,277 searchable across 33 categories
- **Services**: 16 systemd services (all stable)
- **Frontend**: evolvixos.com (landing, studio dashboard, models, APIs, learn hub, developer portal)
- **Security**: JWT auth, OTP, SHA-256 API keys, rate limiting (30/min IP, 100/min API key), SSRF guard

## Discovery Engine
Hourly GitHub scans across 4 repositories:
1. OpenClaw API directory (25,822 APIs)
2. API Mega List (7,000+ APIs)
3. AI Agent Tools (84 tools)
4. Free LLM APIs (442+ models)

## Stack
- **Backend**: Python 3.14, FastAPI-style HTTP servers, SQLite
- **AI**: Ollama (local), Groq (fast), Google Gemini (multimodal), Kimi (reasoning)
- **Cloud**: Tencent Cloud SDK (Python + Go)
- **Infrastructure**: systemd, Nginx, Let's Encrypt SSL, Docker
- **Server**: Hetzner Cloud (16 vCPU, 30GB RAM, 600GB disk)

## License
MIT
