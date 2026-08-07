# AegisOS

**The Universal Autonomous AI Engineering Operating System**

Orchestrate, govern, and scale software systems from intent to production.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                │
│                   Dashboard / Auth / Projects              │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────┐
│                  Backend (FastAPI + Python)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Auth   │  │ Projects │  │   Tasks  │  │  Events  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────────────────────────────────────────────────┐│
│  │              Services (Business Logic)               ││
│  └──────────────────────────────────────────────────────┘│
└────────┬───────────────────────────────────┬────────────┘
         │                                   │
┌────────▼────────┐              ┌───────────▼───────────┐
│  PostgreSQL 16   │              │    Redis 7             │
│  (Data + pgvector)│             │ (Cache + Pub/Sub)     │
└──────────────────┘              └───────────┬──────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  Celery Worker     │
                                    │  (Async Tasks)     │
                                    └───────────────────┘
```

## Tech Stack

- **Backend:** Python 3.11+ FastAPI, SQLAlchemy 2.0, Alembic
- **Frontend:** React 18, Vite 5, Zustand, TanStack Query
- **Database:** PostgreSQL 16 (with pgvector for AI features later)
- **Cache/Queue:** Redis 7, Celery 5
- **Deployment:** Docker Compose
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus metrics at /metrics

## Getting Started

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/Protremix/EvolvixOS.git
cd aegisos

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### Development Mode

```bash
# Start infrastructure (PostgreSQL + Redis)
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
aegisos/
├── backend/
│   ├── app/
│   │   ├── core/          # Config, security, logging, celery
│   │   ├── api/v1/        # API endpoints (auth, users, projects, tasks, events)
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── middleware/    # Error handling
│   │   ├── tasks/         # Celery tasks
│   │   ├── migrations/    # Alembic migrations
│   │   └── main.py        # FastAPI entry point
│   ├── tests/             # Pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/         # Route pages (Login, Dashboard, Projects, Tasks)
│   │   ├── components/     # Reusable components (Sidebar, ProtectedRoute)
│   │   ├── services/      # API client
│   │   └── store/         # Zustand stores
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── .github/workflows/     # CI/CD pipelines
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Register new user
- `POST /api/v1/auth/login` — Login, returns JWT tokens
- `POST /api/v1/auth/refresh` — Refresh access token
- `POST /api/v1/auth/logout` — Logout
- `GET /api/v1/auth/me` — Get current user

### Users
- `GET /api/v1/users/` — List users (admin only)
- `GET /api/v1/users/{id}` — Get user by ID
- `PUT /api/v1/users/{id}` — Update user

### Projects
- `GET /api/v1/projects/` — List projects
- `POST /api/v1/projects/` — Create project (developer+)
- `GET /api/v1/projects/{id}` — Get project
- `PUT /api/v1/projects/{id}` — Update project
- `DELETE /api/v1/projects/{id}` — Soft delete project

### Tasks
- `GET /api/v1/tasks/` — List tasks (optional project_id filter)
- `POST /api/v1/tasks/` — Create task (developer+)
- `GET /api/v1/tasks/{id}` — Get task
- `PUT /api/v1/tasks/{id}` — Update task
- `DELETE /api/v1/tasks/{id}` — Delete task

### Events
- `GET /api/v1/events/` — List events
- `POST /api/v1/events/` — Create event

### Health & Monitoring
- `GET /health` — Health check
- `GET /metrics` — Prometheus metrics

## License

MIT
