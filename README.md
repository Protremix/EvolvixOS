<div align="center">

# 🧬 EvolvixOS

**The open-source, self-hostable AI engineering platform.**

`435+ models` · `59 providers` · `49 tools` · `auto-routing` · `MIT licensed`

[![License: MIT](https://img.shields.io/github/license/Protremix/EvolvixOS?style=for-the-badge&color=007aff)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-350%2B%20passing-34c759?style=for-the-badge)](TEST_REPORT.md)
[![Models](https://img.shields.io/badge/models-435%2B-5856d6?style=for-the-badge)](https://evolvixos.com/models)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ff9500?style=for-the-badge)](CONTRIBUTING.md)

[🌐 Live Platform](https://evolvixos.com) · [⚡ Try Demo](https://evolvixos.com/demo) · [📚 API Docs](https://evolvixos.com/docs) · [💰 Pricing](https://evolvixos.com/pricing) · [🖥️ Dashboard](https://evolvixos.com/dashboard)

</div>

---

## What is EvolvixOS?

EvolvixOS is a self-hostable AI engineering platform — think of it as your own private Base44 / Vercel / Replit for AI. Define data models, deploy agents, orchestrate workflows, and access 435+ AI models through a single API. All from one workstation.

**Why it's different:**
- 🔓 **MIT licensed** — self-host the entire platform, your keys, your data
- 🧠 **435+ models, one endpoint** — auto-routing picks the best model per task (coding → DeepSeek, reasoning → Gemini, chat → Nemotron)
- ⚡ **No data training** — your prompts never train anyone's models
- 🔧 **49 built-in tools** — code execution, file ops, web search, GitHub, crypto, image gen, and more
- 🏗️ **Full platform** — entities (database), backend functions, workflows, file storage, agents
- 🎯 **Zero paid tokens for core** — local Ollama fallback means it runs free

## Quick Start

### Option 1: Use the hosted platform (free)
```bash
# Sign up — get 100 free credits/month, no credit card
# Try the demo first — 5 free requests, no signup:
curl -X POST https://evolvixos.com/platform/api/demo \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a haiku about code"}'
```

### Option 2: Use the SDK
```bash
# Python
pip install evolvixos

# JavaScript
npm install evolvixos
```

```python
from evolvixos import EvolvixOS
client = EvolvixOS(api_key="your-key")
print(client.chat("Hello!"))["response"])
```

### Option 3: Self-host
```bash
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS

# Set required env
export JWT_SECRET="your-secret"

# Optional: Add AI providers (free tiers available)
export GROQ_API_KEY="your-groq-key"      # Free at groq.com
export NVIDIA_API_KEY="your-nvidia-key"  # Free at build.nvidia.com
export OPENROUTER_API_KEY="your-key"     # Free models at openrouter.ai

# Start the platform
pip3 install -r requirements.txt
python3 platform/main.py &    # Platform API on :8080
python3 auth/auth_api.py &     # Auth API on :5000
python3 models/model_api.py &  # Model API on :5010
```

## Core Features

### 🧠 Unified Model Routing
One API call, 435+ models. The router automatically selects the best model for your task.

```python
import requests

resp = requests.post("https://evolvixos.com/platform/api/playground", {
    "message": "Review this code for bugs: def fib(n): return fib(n-1)+fib(n-2)",
    "model": "auto",  # or specify: "deepseek/deepseek-v4-flash-0731"
    "system_prompt": "You are a senior code reviewer.",
    "temperature": 0.3,
    "max_tokens": 1000
}, headers={"Authorization": "Bearer YOUR_API_KEY"})

print(resp.json())
# {"response": "The function is missing a base case...", "model": "deepseek/...", "provider": "openrouter"}
```

**Provider chain (fallback order):**
| # | Provider | Models | Free? | Best For |
|---|----------|--------|-------|----------|
| 1 | NVIDIA | Nemotron-3.5-30B | ✅ | Agentic tasks, reasoning |
| 2 | Groq | Qwen3.8-27B, GPT-OSS-120B | ✅ | Fast inference (467 tok/s) |
| 3 | OpenRouter | 435+ (21 free) | Mixed | Smart auto-routing |
| 4 | Ollama | Qwen2.5:14b/7b/3b | ✅ | Local, offline, zero-cost |

### 📦 Entities (Database)
Define data models as JSON schemas. Get instant CRUD API with pagination, filtering, sorting.

```bash
# Create an entity
curl -X POST https://evolvixos.com/platform/api/entities \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task",
    "schema": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "status": {"type": "string", "enum": ["todo", "doing", "done"]},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]}
      },
      "required": ["title"]
    }
  }'

# Create records
curl -X POST https://evolvixos.com/platform/api/entities/Task/records \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "Ship the demo", "status": "doing", "priority": "high"}'
```

### 🤖 AI Agents
Create autonomous agents with system prompts, tools, and memory.

```bash
# Create an agent
curl -X POST https://evolvixos.com/platform/api/agents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "code-reviewer",
    "system_prompt": "You are a senior code reviewer. Analyze code for bugs, security issues, and improvements.",
    "model": "auto"
  }'

# Chat with your agent
curl -X POST https://evolvixos.com/platform/api/agents/code-reviewer/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Review: def fib(n): return fib(n-1)+fib(n-2)"}'
```

### ⚙️ Workflows
Scheduled and triggered automations that run on entity changes or cron schedules.

```bash
# Create a scheduled workflow
curl -X POST https://evolvixos.com/platform/api/workflows \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily-summary",
    "trigger_type": "scheduled",
    "schedule": "0 9 * * *",
    "definition": {"steps": [...]}
  }'
```

### 🔧 Backend Functions
Deploy Python functions as HTTP endpoints.

```bash
# Deploy a function
curl -X POST https://evolvixos.com/platform/api/functions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "getWeather",
    "code": "def handler(input):\n    return {"city": input.get("city"), "temp": 22}"
  }'

# Call it
curl https://evolvixos.com/platform/api/fn/getWeather?city=Madrid
```

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      EvolvixOS v10 Platform                         │
├──────────────────┬──────────────────┬───────────────────────────────┤
│  Platform API     │  Auth API        │   Model API                   │
│  :8080            │  :5000           │   :5010                       │
│  Entities CRUD    │  JWT + API Keys  │   435+ models                 │
│  Backend Functions│  Rate limiting   │   Auto-routing                │
│  Workflows        │  User isolation  │   59 providers                │
│  File Storage     │  Credits system  │   Fallback chain              │
│  AI Chat Builder  │  Stripe billing  │                               │
├──────────────────┼──────────────────┼───────────────────────────────┤
│  Dashboard        │  Landing Page    │   Demo Playground             │
│  /dashboard       │  /               │   /demo (no signup)           │
│  Dark mode        │  Cinematic 3D    │   5 free req/day              │
│  Model Playground │  Trust bar       │   Auto-routing only          │
│  Agent Manager    │  SEO optimized   │                               │
├──────────────────┴──────────────────┴───────────────────────────────┤
│                    Unified Routing Bridge                            │
│  FreeToken → NVIDIA → Groq → OpenRouter(auto) → V10 → Ollama        │
│  Privacy modes: LOCAL / HYBRID / CLOUD                             │
├────────────────────┬───────────────┬───────────────┬─────────────────┤
│  OpenViking       │  TencentDB     │  GitHub       │  Security       │
│  Context/Memory   │  Agent Memory  │  Discovery    │  350+ tests     │
│  Port 8200        │  3 containers  │  Engine       │  RLS + Audit    │
│  Semantic search  │  Hub + Proxy   │  Auto-learn   │  SSRF/XSS guard │
├────────────────────┴───────────────┴───────────────┴─────────────────┤
│              Infrastructure (18 systemd services)                    │
│  Nginx HTTPS · Let's Encrypt · Ollama · Docker · OpenViking         │
│  Server: Hetzner Cloud (16 vCPU, 30GB RAM, 600GB disk)             │
└─────────────────────────────────────────────────────────────────────┘
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/platform/api/playground` | POST | Chat with any model (auth required) |
| `/platform/api/demo` | POST | Try without signup (5 req/day, no auth) |
| `/platform/api/chat` | POST | Builder chat (creates entities/functions) |
| `/platform/api/models` | GET | List all 435+ models |
| `/platform/api/entities` | POST | Create entity (database table) |
| `/platform/api/entities/{name}/records` | GET/POST | CRUD records |
| `/platform/api/agents` | GET/POST | Create & list AI agents |
| `/platform/api/agents/{name}/chat` | POST | Chat with an agent |
| `/platform/api/functions` | POST | Deploy backend function |
| `/platform/api/fn/{name}` | GET/POST | Call deployed function |
| `/platform/api/workflows` | GET/POST | Create & list workflows |
| `/platform/api/files/upload` | POST | Upload file to storage |
| `/platform/api/credits` | GET | Check credit balance |

Full docs: [evolvixos.com/docs](https://evolvixos.com/docs)

## SDKs

### Python
```python
import requests

BASE = "https://evolvixos.com/platform/api"
TOKEN = "your-api-key"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Chat
r = requests.post(f"{BASE}/playground", json={
    "message": "Explain async/await in Python",
    "model": "auto"
}, headers=headers)
print(r.json()["response"])

# Create entity
r = requests.post(f"{BASE}/entities", json={
    "name": "Post",
    "schema": {"type": "object", "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"}
    }, "required": ["title"]}
}, headers=headers)

# Create record
r = requests.post(f"{BASE}/entities/Post/records", json={
    "title": "Hello World",
    "content": "My first post"
}, headers=headers)
```

### JavaScript
```javascript
const BASE = 'https://evolvixos.com/platform/api';
const TOKEN = 'your-api-key';

// Chat
const resp = await fetch(`${BASE}/playground`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${TOKEN}` },
  body: JSON.stringify({ message: 'Write a React component', model: 'auto' })
});
const data = await resp.json();
console.log(data.response, data.model);
```

### cURL
```bash
# List models
curl https://evolvixos.com/platform/api/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Chat with specific model
curl -X POST https://evolvixos.com/platform/api/playground \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"message":"What is the meaning of life?","model":"auto"}'
```

## Configuration

```bash
# Required
export JWT_SECRET="your-secret"

# AI Providers (all have free tiers)
export GROQ_API_KEY="your-groq-key"        # Free at groq.com
export NVIDIA_API_KEY="your-nvidia-key"    # Free at build.nvidia.com
export OPENROUTER_API_KEY="your-key"       # Free models at openrouter.ai
export GEMINI_API_KEY="your-gemini-key"    # Free at ai.google.dev
export KIMI_API_KEY="your-kimi-key"        # moonshot.ai

# Privacy mode: LOCAL (Ollama only), HYBRID (local+cloud), CLOUD (all)
export EVOLVIX_PRIVACY_MODE="HYBRID"

# Optional: Tencent Cloud
export TENCENTCLOUD_SECRET_ID="your-id"
export TENCENTCLOUD_SECRET_KEY="your-key"

# Payments (optional)
export STRIPE_SECRET_KEY="your-stripe-key"
```

## Platform Stats

| | |
|:---|:---|
| **Models** | 435+ across 59 providers |
| **Tools** | 49 built-in (code, files, web, GitHub, crypto, images) |
| **Tests** | 350+ passing (unit, integration, fuzzing, security) |
| **Services** | 18 systemd services |
| **Server** | Hetzner Cloud (16 vCPU, 30GB RAM, 600GB SSD) |
| **Stack** | Python 3.14, FastAPI, asyncpg, PostgreSQL, Nginx, Docker |
| **License** | MIT — self-host freely |

## Roadmap

- [x] Unified model routing (435+ models, auto-routing)
- [x] Platform API (entities, functions, workflows, agents)
- [x] Dashboard with dark mode
- [x] Model playground
- [x] No-signup demo mode
- [x] Stripe billing integration
- [x] SEO infrastructure (sitemap, robots, JSON-LD)
- [x] Streaming responses (SSE)
- [x] Python SDK package (pip install evolvixos)
- [x] JavaScript SDK package (npm install evolvixos)
- [x] VS Code extension
- [x] Docker Compose one-click deploy
- [x] Kubernetes helm chart

## Contributing

Contributions welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[MIT](LICENSE) — EvolvixOS is free and open-source software.

<div align="center">

**[⭐ Star this repo](https://github.com/Protremix/EvolvixOS)** · **[🍴 Fork](https://github.com/Protremix/EvolvixOS/fork)** · **[⚡ Try Demo](https://evolvixos.com/demo)** · **[🌐 Live Platform](https://evolvixos.com)**

</div>
