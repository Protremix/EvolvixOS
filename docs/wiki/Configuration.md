# Configuration

## Environment Variables

### Core (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET` | Secret for JWT token signing | `your-random-secret` |

### AI Brains (Optional)

| Variable | Description | Engine |
|----------|-------------|--------|
| `GROQ_API_KEY` | Groq API key | Groq (gpt-oss-120b) |
| `GEMINI_API_KEY` | Google Gemini API key | Gemini (3.6 Flash) |
| `KIMI_API_KEY` | Kimi/Moonshot API key | Kimi (moonshot-v1-32k) |

### Tencent Cloud (Optional)

| Variable | Description |
|----------|-------------|
| `TENCENTCLOUD_SECRET_ID` | Tencent Cloud access key ID |
| `TENCENTCLOUD_SECRET_KEY` | Tencent Cloud secret key |

### TIMSDK (Optional)

| Variable | Description |
|----------|-------------|
| `TIM_SDK_APP_ID` | Tencent IM SDK App ID |
| `TIM_SECRET_KEY` | Tencent IM secret key |

### Ollama (Local)

No configuration needed. Ollama runs as a systemd service on `:11434`.

Installed models:
- `qwen2.5:14b` — Full capability
- `qwen2.5:7b` — Balanced
- `qwen2.5:3b` — Fast fallback

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| Model Registry | `models/model_registry.json` | 81 models across 8 categories |
| Tool Definitions | `models/model_api.py` | 44 tool definitions |
| MBTI Profiles | `models/mbti_profiles.py` | 16 personality profiles |
| SSRF Guard | `models/ssrf_guard.py` | SSRF protection |
| Tencent Manager | `models/tencentcloud_manager.py` | Tencent Cloud API |
| Auth System | `auth/auth_api.py` | Authentication API |
| API Keys | `auth/api_keys_system.py` | Per-user API keys |

## Default Ports

| Service | Port |
|---------|------|
| Model API | 5010 |
| Auth API | 5000 |
| Dashboard | 8080 |
| Nginx | 80 / 443 |
| Ollama | 11434 |
| Memory Core | 8420 |
| Memory Hub | 8125 |
| Memory Proxy | 8096 |
