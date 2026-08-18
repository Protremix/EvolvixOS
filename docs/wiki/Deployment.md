# Deployment

## Prerequisites

- Ubuntu 22.04+ server
- Python 3.10+
- Go 1.21+ (for tccli binary)
- Docker (for containers)
- Root access

## Quick Deploy

```bash
git clone https://github.com/Protremix/EvolvixOS.git
cd EvolvixOS
chmod +x gpu_deploy.sh
./gpu_deploy.sh
```

## Manual Setup

### 1. Install Dependencies

```bash
apt update && apt install -y python3 python3-pip golang docker.io nginx
pip3 install -r requirements.txt
```

### 2. Configure Nginx

```nginx
server {
    listen 80;
    server_name evolvixos.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5010;
    }
    
    location /auth/ {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### 3. Create Systemd Services

```bash
# Model API
cat > /etc/systemd/system/evolvix-model-api.service << EOF
[Unit]
Description=EvolvixOS Model API
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/evolvixos/models/model_api.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now evolvix-model-api
```

### 4. SSL with Let's Encrypt

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d evolvixos.com -d www.evolvixos.com
```

### 5. Docker Containers

```bash
# TencentDB Agent Memory
cd /opt/evolvixos/memory
docker-compose up -d

# CubeSandbox
docker build -t evolvix-sandbox /opt/evolvixos/cubesandbox
```

## Verification

```bash
# Check all services
systemctl list-units --type=service | grep evolvix

# Test health
curl http://localhost:5010/api/health

# Test auth
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'
```
