# Local Development Environment

## Quick Start

```bash
./scripts/dev-start.sh    # Start backend + frontend + redis
./scripts/dev-seed.sh     # Seed development data
./scripts/dev-test.sh     # Run all tests
./scripts/dev-stop.sh     # Stop all services
```

## Services

| Service | Port | URL |
|---|---|---|
| AegisOS Backend | 8000 | http://localhost:8000 |
| AegisOS Frontend | 5173 | http://localhost:5173 |
| API Docs | 8000 | http://localhost:8000/docs |
| Redis | 6379 | localhost:6379 |
| PostgreSQL | 5432 | localhost:5432 (optional) |
| Prometheus | 9090 | http://localhost:9090 (optional) |

## Optional Services

```bash
docker compose -f docker-compose.dev.yml --profile postgres up -d
docker compose -f docker-compose.dev.yml --profile monitoring up -d
```

## Non-Docker Development

### Backend
```bash
cd aegisos/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd aegisos/frontend
npm install
npm run dev
```

### Blockchain
```bash
cargo run --release -- --dev --tmp
```

## Environment Variables

Create `.env` in root:
```env
OPENAI_API_KEY_2=your-key
DATABASE_URL=sqlite:///./data/aegisos.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret
DEBUG=true
```

## Default Credentials
| Service | Email | Password |
|---|---|---|
| AegisOS | admin@verdis.io | admin |

## Troubleshooting

### Port in use
```bash
lsof -i :8000
kill -9 <PID>
```

### Docker not running
```bash
systemctl start docker  # Linux
```

*Last updated: August 5, 2026*
