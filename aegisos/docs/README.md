# EvolvixOS — Universal AI Engineering Operating System

> The AI-powered operating system for software engineering. Build, manage, and ship software with autonomous AI agents.

## What is EvolvixOS?

EvolvixOS is a universal AI Engineering Operating System that orchestrates autonomous AI agents to manage the complete software development lifecycle. It provides a unified platform for:

- **Architecture & Design** — AI agents that analyze, plan, and review software architecture
- **Code Quality** — Automated testing, security analysis, performance profiling
- **Pipeline Orchestration** — 10-stage feature delivery pipeline from PRD to release
- **Knowledge Intelligence** — Pattern detection, lesson extraction, best practices
- **Project Management** — Multi-project support with type-specific adapters
- **Monitoring & Analytics** — Real-time dashboards, performance tracking, benchmarks

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EvolvixOS Frontend                      │
│              (React + Vite + TailwindCSS)                 │
├─────────────────────────────────────────────────────────┤
│                    API Gateway (FastAPI)                  │
├──────────────┬──────────────┬───────────────────────────┤
│   Auth & RBAC │   Projects   │    Pipeline Engine         │
│   (JWT+bcrypt)│   & Tasks    │    (10-stage workflow)     │
├──────────────┼──────────────┼───────────────────────────┤
│   AI Agents   │  Knowledge   │    Event Bus (Redis)       │
│   (11 agents) │  Base        │    (WebSocket streaming)   │
├──────────────┼──────────────┼───────────────────────────┤
│   Analytics   │  Dashboard   │    Backup & Restore        │
├──────────────┴──────────────┴───────────────────────────┤
│              PostgreSQL + Redis + Celery                  │
└─────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| 11 AI Agents | CTO, Architect, Security, QA, Planner, Reviewer, Documentation, Memory, Test Generator, CI Healer, Workflow Engine |
| 10-Stage Pipeline | PRD → Architecture → Decomposition → Implementation → QA → Security → Performance → Documentation → Review → Release |
| Knowledge Base | Pattern detection, lesson extraction, best practices library |
| Global Search | Unified search across pipelines, knowledge, activity, webhooks, settings, templates |
| Real-time Events | WebSocket streaming for pipeline events |
| Project Adapters | 7 built-in adapters (blockchain, web, frontend, mobile, infra, AI/ML, generic) |
| Verdis Integration | Live blockchain monitoring, health checks, benchmarking |
| Backup & Restore | Full system state export and selective restore |
| System Settings | 30+ configurable settings across 8 categories |

## Quick Start

```bash
# Clone
git clone https://github.com/Protremix/Verdischain-.git
cd Verdis/evolvixos

# Configure
cp .env.example .env
# Edit .env with your settings

# Deploy (Docker)
docker compose -f docker-compose.prod.yml up -d

# Or develop locally
cd backend && pip install -r requirements.txt
cd frontend && npm install && npm run dev
```

## Documentation

- [Installation Guide](./INSTALLATION.md)
- [Configuration Reference](./CONFIGURATION.md)
- [API Reference](./API_REFERENCE.md)
- [AI Agents Guide](./AI_AGENTS.md)
- [Pipeline Guide](./PIPELINE.md)
- [Frontend Guide](./FRONTEND.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Verdis Integration](./VERDIS_INTEGRATION.md)
- [Developer Guide](./DEVELOPER.md)

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic, Celery
- **Frontend**: React 18, Vite, TailwindCSS
- **Database**: PostgreSQL 16 (with pgvector for AI embeddings)
- **Cache/Events**: Redis 7 (pub/sub event bus)
- **AI**: OpenAI GPT-4o
- **Infrastructure**: Docker, Nginx, systemd

## Stats

- 853 tests passing
- 220 API endpoints across 30 routers
- 33 frontend pages
- 11 AI agents
- 10-stage pipeline
- ~34K lines of code

## License

Part of the Verdis ecosystem. See the main repository for details.

## First Managed Project

EvolvixOS's first managed project is the **Verdis Blockchain** — the world's first fully green, carbon-negative blockchain ecosystem. See [Verdis Integration](./VERDIS_INTEGRATION.md) for details.
