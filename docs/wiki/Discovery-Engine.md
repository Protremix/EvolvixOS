# Discovery Engine

The Discovery Engine is EvolvixOS's automatic learning system. It scans GitHub repositories hourly to discover new APIs, tools, and AI models, then integrates them into the platform's searchable registry.

## How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  GitHub API  │ ──→ │  Parser      │ ──→ │  Registry    │
│  (hourly)    │     │  (markdown   │     │  (JSON)      │
│              │     │   tables)    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ↓
                                         ┌──────────────┐
                                         │  Model API   │
                                         │  /api/models  │
                                         │  /api/apis    │
                                         └──────────────┘
```

## Tracked Repositories

| Repository | Content | Items | Categories |
|-----------|---------|-------|------------|
| OpenClaw API Directory | APIs | 25,822 | 18 |
| API Mega List | APIs | 7,000+ | 15 |
| AI Agent Tools | Tools | 84 | 8 |
| Free LLM APIs | Models | 442+ | 31 |

**Total: 35,277 searchable APIs/tools**

## Systemd Service

```bash
# Status
systemctl status evolvix-discovery

# Logs
journalctl -u evolvix-discovery -f

# Manual run
python3 /opt/evolvixos/learner/discovery_engine.py
```

## API Access

```bash
# Search APIs
curl http://localhost:5010/api/apis?q=weather

# Browse by category
curl http://localhost:5010/api/apis?category=weather

# List all models
curl http://localhost:5010/api/models
```
