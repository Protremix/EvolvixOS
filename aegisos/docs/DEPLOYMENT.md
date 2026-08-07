# Deployment Guide

## Production Architecture

```
Internet → Nginx (SSL/TLS) → Frontend (port 3000)
                          → API (port 8000)
                          → WebSocket (port 8000/ws)
                          → Health (port 8000/api/v1/health)
```

## Prerequisites

- Docker and Docker Compose
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- At least 2GB RAM, 2 CPU cores

## Step 1: Server Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Install Docker Compose
apt install docker-compose-plugin

# Install Nginx
apt install nginx

# Install Certbot
apt install certbot python3-certbot-nginx
```

## Step 2: SSL Certificate

```bash
# Get Let's Encrypt certificate
certbot --nginx -d evolvixos.verdischain.com
```

## Step 3: Deploy EvolvixOS

```bash
# Clone repository
git clone https://github.com/Protremix/Verdischain-.git /opt/evolvixos
cd /opt/evolvixos/evolvixos

# Configure environment
cp .env.example .env
# Edit .env with production values:
# - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
# - ENCRYPTION_KEY (generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
# - POSTGRES_PASSWORD (strong password)
# - OPENAI_API_KEY (your key)

# Build and start
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker exec evolvixos-api python -m alembic upgrade head

# Create admin user
docker exec evolvixos-api python -c "
from app.core.security import get_password_hash
from app.models.user import User
from app.db.session import SessionLocal
db = SessionLocal()
admin = User(email='admin@verdischain.com', full_name='Admin', hashed_password=get_password_hash('YourPassword'), role='admin', is_active=True)
db.add(admin)
db.commit()
"
```

## Step 4: Nginx Configuration

```bash
# Copy nginx config
cp nginx/evolvixos.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/evolvixos.conf /etc/nginx/sites-enabled/

# Test config
nginx -t

# Reload
systemctl reload nginx
```

## Step 5: Systemd Service

```bash
# Copy systemd service
cp deploy/evolvixos.service /etc/systemd/system/

# Enable and start
systemctl daemon-reload
systemctl enable evolvixos
systemctl start evolvixos
```

## Step 6: Verify

```bash
# Health check
curl https://evolvixos.verdischain.com/health

# API docs
curl https://evolvixos.verdischain.com/api/v1/health

# Frontend
# Visit https://evolvixos.verdischain.com
```

## Resource Limits

| Service | Memory | CPU |
|---------|--------|-----|
| PostgreSQL | 512MB | 1.0 |
| Redis | 256MB | 0.5 |
| API | 1GB | 2.0 |
| Worker | 512MB | 1.0 |
| Frontend | 128MB | 0.25 |

## Backup

```bash
# Manual backup via API
curl -X POST https://evolvixos.verdischain.com/api/v1/backup/   -H "Authorization: Bearer <token>"   -d '{"description": "Pre-deployment backup"}'

# Automated backups (add to crontab)
0 2 * * * curl -X POST https://evolvixos.verdischain.com/api/v1/backup/   -H "Authorization: Bearer <token>"   -d '{"description": "Daily automated backup"}'
```

## Monitoring

```bash
# Health check (for monitoring tools)
curl -s https://evolvixos.verdischain.com/health | jq .status

# Detailed health
curl -s https://evolvixos.verdischain.com/api/v1/health/detail   -H "Authorization: Bearer <token>"
```

## Updating

```bash
cd /opt/evolvixos/evolvixos
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker exec evolvixos-api python -m alembic upgrade head
```
