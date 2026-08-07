# Installation Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (recommended)

## Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/verdischain/Verdis.git
cd Verdis/evolvixos

# Copy environment template
cp .env.example .env

# Edit .env with production values:
# - SECRET_KEY (64-char hex string)
# - ENCRYPTION_KEY (Fernet key)
# - POSTGRES_PASSWORD
# - OPENAI_API_KEY

# Build and start
docker compose -f docker-compose.prod.yml up -d

# Run database migrations
docker exec evolvixos-api python -m alembic upgrade head

# Create admin user
docker exec evolvixos-api python -c "
from app.core.security import get_password_hash
from app.models.user import User
from app.db.session import SessionLocal
db = SessionLocal()
admin = User(
    email='admin@example.com',
    full_name='Admin',
    hashed_password=get_password_hash('YourSecurePassword'),
    role='admin',
    is_active=True
)
db.add(admin)
db.commit()
"

# Verify
curl http://localhost:8000/api/v1/health
```

## Option 2: Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/evolvixos"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key"
export OPENAI_API_KEY="your-api-key"

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --port 8000

# Start Celery worker (separate terminal)
celery -A app.worker worker --loglevel=info
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Option 3: Production with Nginx

See the [Deployment Guide](./DEPLOYMENT.md) for full production setup with SSL, Nginx, and systemd.

## Verifying Installation

1. **Health Check**: `GET /api/v1/health` — should return `{"status": "healthy"}`
2. **API Docs**: Visit `http://localhost:8000/docs` for Swagger UI
3. **Frontend**: Visit `http://localhost:3000` (Docker) or `http://localhost:5173` (dev)
4. **Login**: Use the admin credentials you created

## Troubleshooting

### PostgreSQL connection failed
Ensure PostgreSQL is running and the connection string is correct:
```bash
psql -U postgres -h localhost
```

### Redis connection failed
```bash
redis-cli ping  # Should return PONG
```

### OpenAI API errors
Verify your API key has GPT-4o access and sufficient credits.

### Frontend build errors
```bash
cd frontend
rm -rf node_modules .vite
npm install
npm run build
```
