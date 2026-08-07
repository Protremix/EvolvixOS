# EvolvixOS — Universal AI Engineering Operating System

> The AI-powered operating system for software engineering. Build, manage, and ship software with autonomous AI agents.

EvolvixOS orchestrates 11 autonomous AI agents to manage the complete software development lifecycle. It provides pipeline orchestration, knowledge intelligence, project management, monitoring, and analytics — all in one platform.

**First managed project:** [Verdis Blockchain](https://verdischain.com) — the world's first fully green, carbon-negative blockchain ecosystem.

## Quick Start

```bash
# Clone
git clone https://github.com/verdischain/Verdis.git
cd Verdis/evolvixos

# Configure
cp .env.example .env  # Edit with your values

# Deploy (Docker)
docker compose -f docker-compose.prod.yml up -d
docker exec evolvixos-api python -m alembic upgrade head
```

## Documentation

Full documentation is in [`docs/`](./docs/):
- [Overview](./docs/README.md) — What EvolvixOS is and what it does
- [Installation](./docs/INSTALLATION.md) — Setup guide (Docker, local, production)
- [Configuration](./docs/CONFIGURATION.md) — All environment variables and system settings
- [API Reference](./docs/API_REFERENCE.md) — 220 endpoints across 30 routers
- [AI Agents](./docs/AI_AGENTS.md) — 11 AI agents and how to use them
- [Pipeline Guide](./docs/PIPELINE.md) — 10-stage feature delivery pipeline
- [Frontend Guide](./docs/FRONTEND.md) — 33 pages, React architecture
- [Deployment](./docs/DEPLOYMENT.md) — Production setup with SSL, Nginx, systemd
- [Verdis Integration](./docs/VERDIS_INTEGRATION.md) — Blockchain monitoring and management
- [Developer Guide](./docs/DEVELOPER.md) — Project structure, adding features

## Stats

| Metric | Value |
|--------|-------|
| Tests | 853 passing |
| API Endpoints | 220 across 30 routers |
| Frontend Pages | 33 |
| AI Agents | 11 |
| Pipeline Stages | 10 |
| Code Lines | ~34K (Python + React) |
| Documentation | 10 files, 44K words |

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Alembic, Celery
- **Frontend:** React 18, Vite, TailwindCSS
- **Database:** PostgreSQL 16
- **Cache/Events:** Redis 7
- **AI:** OpenAI GPT-4o
- **Infrastructure:** Docker, Nginx, systemd

## License

Part of the Verdis ecosystem. See the main repository.
