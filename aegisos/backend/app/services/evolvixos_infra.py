"""
EvolvixOS Infrastructure — Separate Domain & Server

Manages EvolvixOS as an independent platform on evolvixos.com
with its own server, DNS, SSL, and deployment pipeline.
"""

import secrets
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("service.evolvixos_infra")


class ServiceStatus(str, Enum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    CONFIGURING = "configuring"
    DEPLOYING = "deploying"
    LIVE = "live"
    ERROR = "error"


class ComponentType(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    REDIS = "redis"
    NGINX = "nginx"
    MONITORING = "monitoring"
    DOCKER = "docker"


@dataclass
class EvolvixOSComponent:
    id: str
    name: str
    type: str
    port: int
    status: str = ServiceStatus.PENDING.value
    health_url: str = ""
    docker_image: str = ""
    environment_vars: list = field(default_factory=list)
    depends_on: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvolvixOSDNSSubdomain:
    id: str
    subdomain: str
    full_domain: str
    target: str  # IP or CNAME target
    record_type: str = "A"
    description: str = ""
    ttl: int = 3600

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvolvixOSDeploymentStep:
    id: str
    order: int
    name: str
    description: str
    command: str = ""
    script: str = ""
    expected_time: str = ""
    status: str = ServiceStatus.PENDING.value
    depends_on: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class EvolvixOSInfraService:
    """Manages EvolvixOS as a separate platform."""

    DOMAIN = "evolvixos.com"
    SERVER_IP = "PLACEHOLDER_IP"  # Replace when server is provisioned

    def __init__(self):
        self._components: dict[str, EvolvixOSComponent] = {}
        self._dns_records: dict[str, EvolvixOSDNSSubdomain] = {}
        self._deploy_steps: dict[str, EvolvixOSDeploymentStep] = {}
        self._init_components()
        self._init_dns()
        self._init_steps()

    def _init_components(self):
        """Initialize EvolvixOS components."""
        components = [
            ("EvolvixOS Frontend", ComponentType.FRONTEND.value, 3000, "http://localhost:3000", "evolvixos/frontend:latest"),
            ("EvolvixOS Backend", ComponentType.BACKEND.value, 8000, "http://localhost:8000/health", "evolvixos/backend:latest"),
            ("PostgreSQL", ComponentType.DATABASE.value, 5432, "", "postgres:16-alpine"),
            ("Redis", ComponentType.REDIS.value, 6379, "", "redis:7-alpine"),
            ("Nginx", ComponentType.NGINX.value, 80, "http://localhost/health", "nginx:alpine"),
            ("Prometheus", ComponentType.MONITORING.value, 9090, "http://localhost:9090/-/healthy", "prom/prometheus:latest"),
            ("Grafana", ComponentType.MONITORING.value, 3001, "http://localhost:3001/api/health", "grafana/grafana:latest"),
        ]
        for name, ctype, port, health, image in components:
            cid = f"cmp-{secrets.token_hex(8)}"
            env_vars = []
            if ctype == ComponentType.BACKEND.value:
                env_vars = [
                    "DATABASE_URL=postgresql://evolvixos:password@postgres:5432/evolvixos",
                    "REDIS_URL=redis://redis:6379/0",
                    "SECRET_KEY=<generate>",
                    "JWT_SECRET=<generate>",
                    "ENVIRONMENT=production",
                    "VERDIS_RPC_URL=https://rpc.verdischain.com",
                    "VERDIS_API_URL=https://api.verdischain.com",
                    "CORS_ORIGINS=https://evolvixos.com,https://www.evolvixos.com",
                ]
            elif ctype == ComponentType.FRONTEND.value:
                env_vars = [
                    "VITE_API_URL=https://api.evolvixos.com",
                    "VITE_WS_URL=wss://ws.evolvixos.com",
                    "VITE_VERDIS_RPC=https://rpc.verdischain.com",
                ]
            self._components[cid] = EvolvixOSComponent(
                id=cid, name=name, type=ctype, port=port,
                health_url=health, docker_image=image,
                environment_vars=env_vars,
            )

    def _init_dns(self):
        """Initialize EvolvixOS DNS records."""
        subdomains = [
            ("", "evolvixos.com", "A", "Main domain — Frontend + EvolvixOS dashboard"),
            ("www", "www.evolvixos.com", "A", "WWW redirect"),
            ("api", "api.evolvixos.com", "A", "Backend API"),
            ("ws", "ws.evolvixos.com", "A", "WebSocket"),
            ("monitor", "monitor.evolvixos.com", "A", "Grafana monitoring"),
            ("docs", "docs.evolvixos.com", "A", "API documentation"),
        ]
        for sub, full, rtype, desc in subdomains:
            did = f"dns-{secrets.token_hex(8)}"
            self._dns_records[did] = EvolvixOSDNSSubdomain(
                id=did, subdomain=sub, full_domain=full,
                target=self.SERVER_IP, record_type=rtype, description=desc,
            )

    def _init_steps(self):
        """Initialize EvolvixOS deployment steps."""
        steps = [
            (1, "Register Domain", "Register evolvixos.com", "Purchase evolvixos.com from domain registrar", "5 min", []),
            (2, "Provision Server", "Provision Ubuntu 22.04 server (16GB RAM, 8 cores)", "Use Hetzner/DigitalOcean/AWS", "30 min", []),
            (3, "Configure DNS", "Point evolvixos.com subdomains to server IP", "bash evolvixos_setup_dns.sh", "10 min", [1, 2]),
            (4, "Harden Server", "Security hardening", "bash evolvixos_harden.sh", "15 min", [2]),
            (5, "Install Docker", "Install Docker and Docker Compose", "curl -fsSL get.docker.com | sh", "5 min", [4]),
            (6, "SSL Certificates", "Obtain Let's Encrypt certs for evolvixos.com", "bash evolvixos_setup_ssl.sh", "10 min", [3, 4]),
            (7, "Clone Repository", "Clone EvolvixOS repo", "git clone https://github.com/verdischain/Verdis.git /opt/evolvixos", "2 min", [5]),
            (8, "Configure Environment", "Edit .env with production values", "nano /opt/evolvixos/evolvixos/backend/.env", "5 min", [7]),
            (9, "Build Docker Images", "Build EvolvixOS images", "docker compose -f evolvixos-docker-compose.yml build", "10 min", [5, 7]),
            (10, "Deploy Services", "Start all EvolvixOS services", "bash evolvixos_deploy.sh", "5 min", [8, 9]),
            (11, "Configure Nginx", "Set up reverse proxy with SSL", "sudo cp evolvixos-nginx.conf /etc/nginx/ && sudo systemctl restart nginx", "5 min", [6, 10]),
            (12, "Health Checks", "Verify all services", "bash evolvixos_health_check.sh", "2 min", [10, 11]),
            (13, "Setup Monitoring", "Install Prometheus + Grafana", "bash evolvixos_setup_monitoring.sh", "15 min", [10]),
            (14, "Setup Backups", "Configure automated backups", "bash evolvixos_setup_backup.sh", "5 min", [10]),
            (15, "Connect to Verdis", "Verify EvolvixOS can reach Verdis API", "curl https://api.verdischain.com/health", "2 min", [12]),
            (16, "Final Verification", "Verify evolvixos.com is live over HTTPS", "curl -vI https://evolvixos.com", "5 min", [11, 12]),
        ]
        for order, name, desc, cmd, est, deps in steps:
            sid = f"stp-{secrets.token_hex(8)}"
            self._deploy_steps[sid] = EvolvixOSDeploymentStep(
                id=sid, order=order, name=name, description=desc,
                command=cmd, expected_time=est, depends_on=deps,
            )

    # === Components ===

    def list_components(self) -> list[EvolvixOSComponent]:
        return list(self._components.values())

    def get_component(self, cid: str) -> Optional[EvolvixOSComponent]:
        return self._components.get(cid)

    def update_component_status(self, cid: str, status: str) -> Optional[EvolvixOSComponent]:
        c = self._components.get(cid)
        if c:
            c.status = status
            return c
        return None

    # === DNS ===

    def list_dns(self) -> list[EvolvixOSDNSSubdomain]:
        return list(self._dns_records.values())

    def get_dns(self, did: str) -> Optional[EvolvixOSDNSSubdomain]:
        return self._dns_records.get(did)

    def set_server_ip(self, ip: str):
        """Update all DNS records with the actual server IP."""
        self.SERVER_IP = ip
        for dns in self._dns_records.values():
            dns.target = ip

    # === Steps ===

    def list_steps(self) -> list[EvolvixOSDeploymentStep]:
        return sorted(self._deploy_steps.values(), key=lambda s: s.order)

    def get_step(self, sid: str) -> Optional[EvolvixOSDeploymentStep]:
        return self._deploy_steps.get(sid)

    def update_step_status(self, sid: str, status: str) -> Optional[EvolvixOSDeploymentStep]:
        s = self._deploy_steps.get(sid)
        if s:
            s.status = status
            return s
        return None

    def get_progress(self) -> dict:
        total = len(self._deploy_steps)
        completed = sum(1 for s in self._deploy_steps.values() if s.status == ServiceStatus.LIVE.value)
        return {
            "total": total,
            "completed": completed,
            "percentage": round(completed / max(1, total) * 100, 1),
            "domain": self.DOMAIN,
            "server_ip": self.SERVER_IP,
        }

    # === Scripts ===

    def get_deployment_scripts(self) -> dict:
        """Generate all EvolvixOS deployment scripts."""
        return {
            "evolvixos_setup_dns.sh": self._dns_script(),
            "evolvixos_harden.sh": self._harden_script(),
            "evolvixos_setup_ssl.sh": self._ssl_script(),
            "evolvixos_deploy.sh": self._deploy_script(),
            "evolvixos_setup_monitoring.sh": self._monitoring_script(),
            "evolvixos_setup_backup.sh": self._backup_script(),
            "evolvixos_health_check.sh": self._health_script(),
            "evolvixos-nginx.conf": self._nginx_config(),
            "evolvixos-docker-compose.yml": self._docker_compose(),
            "evolvixos-systemd.service": self._systemd_config(),
        }

    def _dns_script(self) -> str:
        return f"""#!/bin/bash
set -e
echo "=== EvolvixOS DNS Configuration ==="
echo "Domain: {self.DOMAIN}"
echo "Server IP: ${{SERVER_IP:-{self.SERVER_IP}}}"
echo ""
echo "Configure these DNS records:"
echo "A    evolvixos.com        ${{SERVER_IP:-YOUR_IP}}    3600"
echo "A    www.evolvixos.com    ${{SERVER_IP:-YOUR_IP}}    3600"
echo "A    api.evolvixos.com    ${{SERVER_IP:-YOUR_IP}}    3600"
echo "A    ws.evolvixos.com     ${{SERVER_IP:-YOUR_IP}}    3600"
echo "A    monitor.evolvixos.com ${{SERVER_IP:-YOUR_IP}}   3600"
echo "A    docs.evolvixos.com   ${{SERVER_IP:-YOUR_IP}}    3600"
echo ""
echo "Verify: dig +short A evolvixos.com"
echo "Wait 5-30 min for propagation."
"""

    def _harden_script(self) -> str:
        return """#!/bin/bash
set -e
echo "=== EvolvixOS Server Hardening ==="
sudo apt-get update -qq && sudo apt-get upgrade -y
sudo apt-get install -y ufw fail2ban unattended-upgrades curl wget git

# Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# SSH hardening
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Auto security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Timezone
sudo timedatectl set-timezone Europe/Madrid

# Create evolvixos user
if ! id -u evolvixos &>/dev/null; then
  sudo useradd -m -s /bin/bash evolvixos
  sudo usermod -aG docker evolvixos
fi

echo "=== Hardening Complete ==="
"""

    def _ssl_script(self) -> str:
        return f"""#!/bin/bash
set -e
echo "=== EvolvixOS SSL Setup ==="
sudo apt-get install -y certbot python3-certbot-nginx

DOMAINS=(
  "{self.DOMAIN}"
  "www.{self.DOMAIN}"
  "api.{self.DOMAIN}"
  "ws.{self.DOMAIN}"
  "monitor.{self.DOMAIN}"
  "docs.{self.DOMAIN}"
)

for domain in "${{DOMAINS[@]}}"; do
  echo "Obtaining certificate for $domain..."
  sudo certbot --nginx -d "$domain" --non-interactive --agree-tos \\
    --email admin@{self.DOMAIN} --redirect
done

# Auto-renewal
(sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet") | sudo crontab -
sudo certbot renew --dry-run
echo "=== SSL Setup Complete ==="
"""

    def _deploy_script(self) -> str:
        return f"""#!/bin/bash
set -e
echo "=== EvolvixOS Deployment ==="

sudo mkdir -p /opt/evolvixos
sudo chown evolvixos:evolvixos /opt/evolvixos
cd /opt/evolvixos

if [ ! -d "Verdis" ]; then
  git clone https://github.com/verdischain/Verdis.git
fi
cd Verdis

# Configure environment
cp evolvixos/backend/.env.example evolvixos/backend/.env
echo "Edit .env with production values:"
echo "  - Generate SECRET_KEY and JWT_SECRET"
echo "  - Set DATABASE_URL with strong password"
echo "  - Set VERDIS_RPC_URL=https://rpc.verdischain.com"
echo "  - Set CORS_ORIGINS=https://{self.DOMAIN}"
nano evolvixos/backend/.env

# Build and start
echo "Building Docker images..."
docker compose -f evolvixos-docker-compose.yml build

echo "Starting services..."
docker compose -f evolvixos-docker-compose.yml up -d

sleep 15

# Health checks
echo "Health checks..."
curl -sf http://localhost:8000/health && echo "Backend: OK" || echo "Backend: FAIL"
curl -sf http://localhost:3000 && echo "Frontend: OK" || echo "Frontend: FAIL"

# Systemd
sudo cp evolvixos-systemd.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable evolvixos

echo "=== EvolvixOS Deployed ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Public: https://{self.DOMAIN}"
"""

    def _monitoring_script(self) -> str:
        return """#!/bin/bash
set -e
echo "=== EvolvixOS Monitoring Setup ==="
sudo apt-get install -y prometheus prometheus-node-exporter grafana

sudo tee /etc/prometheus/prometheus.yml > /dev/null << 'PROM'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'evolvixos'
    static_configs:
      - targets: ['localhost:8000']
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
PROM

sudo systemctl restart prometheus
sudo systemctl enable prometheus
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3001 (admin/admin)"
echo "=== Monitoring Complete ==="
"""

    def _backup_script(self) -> str:
        return """#!/bin/bash
set -e
echo "=== EvolvixOS Backup Setup ==="
sudo mkdir -p /opt/backups/evolvixos/postgres
sudo chown -R evolvixos:evolvixos /opt/backups

sudo tee /opt/evolvixos/backup.sh > /dev/null << 'BACKUP'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec evolvixos-postgres pg_dump -U evolvixos evolvixos > /opt/backups/evolvixos/postgres/db_$DATE.sql
find /opt/backups/evolvixos/postgres -name "*.sql" -mtime +7 -delete
echo "Backup: $DATE"
BACKUP

sudo chmod +x /opt/evolvixos/backup.sh
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/evolvixos/backup.sh >> /var/log/evolvixos-backup.log 2>&1") | sudo crontab -
/opt/evolvixos/backup.sh
echo "=== Backup Setup Complete ==="
"""

    def _health_script(self) -> str:
        return f"""#!/bin/bash
echo "=== EvolvixOS Health Check ==="
echo "Time: $(date)"
echo ""
echo "--- Docker Services ---"
docker compose -f /opt/evolvixos/Verdis/evolvixos-docker-compose.yml ps
echo ""
echo "--- Backend ---"
curl -sf http://localhost:8000/health && echo "Backend: HEALTHY" || echo "Backend: UNREACHABLE"
echo ""
echo "--- Frontend ---"
curl -sf http://localhost:3000 >/dev/null && echo "Frontend: HEALTHY" || echo "Frontend: UNREACHABLE"
echo ""
echo "--- Verdis Connection ---"
curl -sf https://rpc.verdischain.com -X POST -H "Content-Type: application/json" \\
  -d '{{"jsonrpc":"2.0","method":"system_health","params":[],"id":1}}' && echo "Verdis: CONNECTED" || echo "Verdis: UNREACHABLE"
echo ""
echo "--- SSL ---"
echo | openssl s_client -connect {self.DOMAIN}:443 -servername {self.DOMAIN} 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "SSL: Check failed"
echo ""
echo "--- Disk ---"
df -h / | head -2
echo ""
echo "--- Memory ---"
free -h | head -2
echo ""
echo "=== Health Check Complete ==="
"""

    def _nginx_config(self) -> str:
        return f"""# EvolvixOS Nginx Configuration
upstream evolvixos_backend {{
    server 127.0.0.1:8000;
}}

upstream evolvixos_frontend {{
    server 127.0.0.1:3000;
}}

# Main domain — Frontend
server {{
    listen 80;
    server_name {self.DOMAIN} www.{self.DOMAIN};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {self.DOMAIN} www.{self.DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{self.DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.DOMAIN}/privkey.pem;
    ssl_protocols TLS 1.2 TLS 1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {{
        proxy_pass http://evolvixos_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}

# API subdomain
server {{
    listen 443 ssl http2;
    server_name api.{self.DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{self.DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.DOMAIN}/privkey.pem;

    location / {{
        proxy_pass http://evolvixos_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }}
}}

# WebSocket subdomain
server {{
    listen 443 ssl http2;
    server_name ws.{self.DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{self.DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.DOMAIN}/privkey.pem;

    location / {{
        proxy_pass http://evolvixos_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}

# Monitoring subdomain
server {{
    listen 443 ssl http2;
    server_name monitor.{self.DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{self.DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.DOMAIN}/privkey.pem;

    location / {{
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
    }}
}}

# Docs subdomain
server {{
    listen 443 ssl http2;
    server_name docs.{self.DOMAIN};

    ssl_certificate /etc/letsencrypt/live/{self.DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.DOMAIN}/privkey.pem;

    location / {{
        proxy_pass http://evolvixos_backend/docs;
        proxy_set_header Host $host;
    }}
}}
"""

    def _docker_compose(self) -> str:
        return """# EvolvixOS Docker Compose — Standalone
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: evolvixos-postgres
    environment:
      POSTGRES_USER: evolvixos
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me_in_prod}
      POSTGRES_DB: evolvixos
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U evolvixos"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: evolvixos-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
    volumes:
      - redis_data:/data

  backend:
    build: ./evolvixos/backend
    container_name: evolvixos-backend
    environment:
      - DATABASE_URL=postgresql://evolvixos:${POSTGRES_PASSWORD:-change_me_in_prod}@postgres:5432/evolvixos
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-generate_me}
      - JWT_SECRET=${JWT_SECRET:-generate_me}
      - ENVIRONMENT=production
      - VERDIS_RPC_URL=https://rpc.verdischain.com
      - VERDIS_API_URL=https://api.verdischain.com
      - CORS_ORIGINS=https://evolvixos.com,https://www.evolvixos.com
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build: ./evolvixos/frontend
    container_name: evolvixos-frontend
    environment:
      - VITE_API_URL=https://api.evolvixos.com
      - VITE_WS_URL=wss://ws.evolvixos.com
      - VITE_VERDIS_RPC=https://rpc.verdischain.com
    depends_on:
      - backend
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
"""

    def _systemd_config(self) -> str:
        return """[Unit]
Description=EvolvixOS AI Engineering Platform
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/evolvixos/Verdis
ExecStart=/usr/bin/docker compose -f evolvixos-docker-compose.yml up -d
ExecStop=/usr/bin/docker compose -f evolvixos-docker-compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
"""

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "domain": self.DOMAIN,
            "server_ip": self.SERVER_IP,
            "components": [c.to_dict() for c in self.list_components()],
            "dns_records": [d.to_dict() for d in self.list_dns()],
            "steps": [s.to_dict() for s in self.list_steps()],
            "progress": self.get_progress(),
            "verdis_connection": {
                "rpc_url": "https://rpc.verdischain.com",
                "api_url": "https://api.verdischain.com",
                "explorer_url": "https://explorer.verdischain.com",
                "status": "configured",
            },
        }


_service: Optional[EvolvixOSInfraService] = None

def get_evolvixos_infra_service() -> EvolvixOSInfraService:
    global _service
    if _service is None:
        _service = EvolvixOSInfraService()
    return _service
