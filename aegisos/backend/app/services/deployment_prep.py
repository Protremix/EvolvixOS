"""
Deployment Preparation — Phase 52

Automated deployment scripts, DNS configuration, SSL setup,
server hardening, and step-by-step deployment guide.
All scripts generated so Rojs can run them on the server.
"""

import secrets
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("service.deployment_prep")


class ScriptType(str, Enum):
    DNS = "dns"
    SSL = "ssl"
    DEPLOY = "deploy"
    HARDENING = "hardening"
    MONITORING = "monitoring"
    BACKUP = "backup"
    ROLLBACK = "rollback"
    HEALTH_CHECK = "health_check"


class ScriptStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DeployScript:
    id: str
    name: str
    type: str
    filename: str
    description: str
    content: str = ""
    commands: list = field(default_factory=list)
    expected_output: str = ""
    timeout: int = 300
    requires_root: bool = False
    status: str = ScriptStatus.READY.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    run_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DNSRecord:
    id: str
    type: str  # A, CNAME, MX, TXT
    name: str
    value: str
    ttl: int = 3600
    priority: int = 0
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SSLConfig:
    id: str
    domain: str
    cert_path: str
    key_path: str
    issuer: str = "Let's Encrypt"
    expiry: str = ""
    auto_renew: bool = True
    commands: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DeploymentStep:
    id: str
    order: int
    name: str
    description: str
    command: str = ""
    script: str = ""
    expected_time: str = ""
    required: bool = True
    status: str = ScriptStatus.PENDING.value
    depends_on: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class DeploymentPrepService:
    """Deployment preparation and automation."""

    def __init__(self):
        self._scripts: dict[str, DeployScript] = {}
        self._dns_records: dict[str, DNSRecord] = {}
        self._ssl_configs: dict[str, SSLConfig] = {}
        self._steps: dict[str, DeploymentStep] = {}
        self._init_scripts()
        self._init_dns()
        self._init_ssl()
        self._init_steps()

    def _init_scripts(self):
        """Initialize deployment scripts."""
        scripts = [
            ("DNS Setup", ScriptType.DNS.value, "setup_dns.sh",
             "Configure DNS records for verdischain.com and subdomains",
             """#!/bin/bash
set -e

# DNS Configuration for verdischain.com
# Run these commands on your DNS provider (Cloudflare, Route53, etc.)

echo "=== DNS Configuration ==="
echo "Configure the following DNS records:"

# Main domain
echo "A    verdischain.com        -> YOUR_SERVER_IP    3600"
echo "A    www.verdischain.com    -> YOUR_SERVER_IP    3600"
echo "A    api.verdischain.com    -> YOUR_SERVER_IP    3600"
echo "A    explorer.verdischain.com -> YOUR_SERVER_IP  3600"
echo "A    faucet.verdischain.com -> YOUR_SERVER_IP    3600"
echo "A    ws.verdischain.com     -> YOUR_SERVER_IP    3600"
echo "CNAME rpc.verdischain.com  -> verdischain.com    3600"

# TXT records
echo "TXT  verdischain.com       -> \"v=spf1 include:_spf.verdischain.com ~all\""
echo "TXT  _dmarc.verdischain.com -> \"v=DMARC1; p=quarantine; rua=mailto:admin@verdischain.com\""

echo ""
echo "=== DNS Verification ==="
echo "dig A verdischain.com"
echo "dig A api.verdischain.com"
echo "dig A explorer.verdischain.com"
echo ""
echo "Wait 5-30 minutes for DNS propagation."
echo "Verify with: dig +short A verdischain.com""",
             ["dig A verdischain.com", "dig A api.verdischain.com"],
             "DNS records resolving to server IP",
             60, False),

            ("SSL Certificate Setup", ScriptType.SSL.value, "setup_ssl.sh",
             "Install Let's Encrypt SSL certificates with auto-renewal",
             """#!/bin/bash
set -e

echo "=== SSL Certificate Setup ==="

# Install certbot
sudo apt-get update -qq
sudo apt-get install -y certbot python3-certbot-nginx

# Obtain certificates for all domains
DOMAINS=(
  "verdischain.com"
  "www.verdischain.com"
  "api.verdischain.com"
  "explorer.verdischain.com"
  "faucet.verdischain.com"
  "ws.verdischain.com"
)

for domain in "${DOMAINS[@]}"; do
  echo "Obtaining certificate for $domain..."
  sudo certbot --nginx -d "$domain" --non-interactive --agree-tos \\
    --email admin@verdischain.com --redirect
done

# Set up auto-renewal
echo "Setting up auto-renewal..."
sudo crontab -l 2>/dev/null | { cat; echo "0 3 * * * certbot renew --quiet"; } | sudo crontab -

# Test renewal
sudo certbot renew --dry-run

echo "=== SSL Setup Complete ==="
echo "Certificates location: /etc/letsencrypt/live/verdischain.com/"
echo "Auto-renewal: Every day at 3 AM"
echo ""
echo "Verify: curl -vI https://verdischain.com 2>&1 | grep SSL""",
             ["certbot --nginx -d verdischain.com", "certbot renew --dry-run"],
             "SSL certificates installed and auto-renewing",
             300, True),

            ("Server Hardening", ScriptType.HARDENING.value, "harden_server.sh",
             "Harden server security: firewall, SSH, fail2ban, updates",
             """#!/bin/bash
set -e

echo "=== Server Hardening ==="

# Update system
sudo apt-get update -qq && sudo apt-get upgrade -y

# Install essential packages
sudo apt-get install -y ufw fail2ban unattended-upgrades htop curl wget git

# Configure UFW firewall
echo "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp        # SSH
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS
sudo ufw allow 30333/tcp     # Verdis P2P
sudo ufw allow 9933/tcp      # Verdis RPC
sudo ufw allow 9944/tcp      # Verdis WebSocket
sudo ufw --force enable

# Configure SSH
echo "Hardening SSH..."
sudo sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/#Port.*/Port 22/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Configure fail2ban
echo "Configuring fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Enable automatic security updates
echo "Enabling automatic security updates..."
sudo dpkg-reconfigure -plow unattended-upgrades

# Set timezone
sudo timedatectl set-timezone Europe/Madrid

# Create verdis user
if ! id -u verdis &>/dev/null; then
  sudo useradd -m -s /bin/bash verdis
  sudo usermod -aG docker verdis
  echo "Created verdis user. Add SSH keys to /home/verdis/.ssh/authorized_keys"
fi

echo "=== Hardening Complete ==="
echo "Firewall: Active (SSH, HTTP, HTTPS, Verdis ports)"
echo "SSH: Key-only auth, no root login"
echo "fail2ban: Active"
echo "Auto-updates: Enabled"
echo "Timezone: Europe/Madrid" """,
             ["ufw status", "fail2ban-client status", "systemctl status sshd"],
             "All hardening measures active",
             180, True),

            ("Deploy Verdis + EvolvixOS", ScriptType.DEPLOY.value, "deploy.sh",
             "Deploy all services using Docker Compose",
             """#!/bin/bash
set -e

echo "=== Verdis + EvolvixOS Deployment ==="

# Create directories
sudo mkdir -p /opt/verdis
sudo chown verdis:verdis /opt/verdis
cd /opt/verdis

# Clone repository
if [ ! -d "Verdis" ]; then
  git clone https://github.com/Protremix/Verdischain-.git
fi
cd Verdis

# Copy manifests
cp evolvixos/backend/.env.example .env
echo "Edit .env with production values"
nano .env

# Build Verdis node
echo "Building Verdis node..."
cd verdis
cargo build --release
sudo cp target/release/verdis-node /usr/local/bin/
cd ..

# Build Docker images
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build

# Start services
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 15

# Health checks
echo "Running health checks..."
curl -sf http://localhost:8000/health && echo "Backend: OK" || echo "Backend: FAIL"
curl -sf http://localhost:3000 && echo "Frontend: OK" || echo "Frontend: FAIL"
curl -sf http://localhost:9933/health && echo "Verdis Node: OK" || echo "Verdis Node: FAIL"

# Setup systemd
echo "Setting up systemd services..."
sudo cp verdis-node.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable verdis-node
sudo systemctl start verdis-node

# Configure nginx
echo "Configuring nginx..."
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx

echo "=== Deployment Complete ==="
echo "Verdis node: http://localhost:9933"
echo "EvolvixOS API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Public: https://verdischain.com"
echo ""
echo "Check status: docker compose -f docker-compose.prod.yml ps\" """,
             ["docker compose -f docker-compose.prod.yml up -d", "curl -sf http://localhost:8000/health"],
             "All services running and healthy",
             600, True),

            ("Monitoring Setup", ScriptType.MONITORING.value, "setup_monitoring.sh",
             "Install Prometheus, Grafana, and configure alerts",
             """#!/bin/bash
set -e

echo "=== Monitoring Setup ==="

# Install Prometheus
sudo apt-get install -y prometheus prometheus-node-exporter

# Install Grafana
sudo apt-get install -y grafana

# Configure Prometheus
sudo tee /etc/prometheus/prometheus.yml > /dev/null << 'PROM'
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'verdis'
    static_configs:
      - targets: ['localhost:9933']
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

# Default Grafana port: 3001 (avoid conflict with frontend)
sudo sed -i 's/3000/3001/' /etc/grafana/grafana.ini
sudo systemctl restart grafana-server

echo "=== Monitoring Complete ==="
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3001 (admin/admin)"
echo "Node Exporter: http://localhost:9100" """,
             ["systemctl status prometheus", "systemctl status grafana-server"],
             "Prometheus and Grafana running",
             180, True),

            ("Backup Setup", ScriptType.BACKUP.value, "setup_backup.sh",
             "Configure automated backups for database and blockchain data",
             """#!/bin/bash
set -e

echo "=== Backup Setup ==="

# Create backup directory
sudo mkdir -p /opt/backups/verdis
sudo mkdir -p /opt/backups/postgres
sudo chown -R verdis:verdis /opt/backups

# Create backup script
sudo tee /opt/verdis/backup.sh > /dev/null << 'BACKUP'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec evolvixos-postgres pg_dump -U postgres evolvixos > /opt/backups/postgres/evolvixos_$DATE.sql

# Backup Verdis blockchain data
tar -czf /opt/backups/verdis/verdis_chain_$DATE.tar.gz /opt/verdis/data/

# Keep only last 7 days
find /opt/backups/postgres -name "*.sql" -mtime +7 -delete
find /opt/backups/verdis -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
BACKUP

sudo chmod +x /opt/verdis/backup.sh

# Schedule daily backup at 2 AM
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/verdis/backup.sh >> /var/log/verdis-backup.log 2>&1") | sudo crontab -

# Run initial backup
/opt/verdis/backup.sh

echo "=== Backup Setup Complete ==="
echo "Schedule: Daily at 2 AM"
echo "Retention: 7 days"
echo "Location: /opt/backups/"
echo "PostgreSQL: /opt/backups/postgres/"
echo "Blockchain: /opt/backups/verdis/" """,
             ["/opt/verdis/backup.sh", "ls /opt/backups/"],
             "Backup script created and scheduled",
             120, True),

            ("Rollback Script", ScriptType.ROLLBACK.value, "rollback.sh",
             "Rollback deployment to previous version",
             """#!/bin/bash
set -e

echo "=== Rollback Procedure ==="

# Stop services
echo "Stopping services..."
docker compose -f docker-compose.prod.yml down

# Restore database from latest backup
LATEST_DB=$(ls -t /opt/backups/postgres/*.sql 2>/dev/null | head -1)
if [ -n "$LATEST_DB" ]; then
  echo "Restoring database from $LATEST_DB..."
  docker exec -i evolvixos-postgres psql -U postgres evolvixos < "$LATEST_DB"
fi

# Restore blockchain data
LATEST_CHAIN=$(ls -t /opt/backups/verdis/*.tar.gz 2>/dev/null | head -1)
if [ -n "$LATEST_CHAIN" ]; then
  echo "Restoring blockchain data from $LATEST_CHAIN..."
  tar -xzf "$LATEST_CHAIN" -C /
fi

# Restart services
echo "Restarting services..."
docker compose -f docker-compose.prod.yml up -d

# Health checks
sleep 15
curl -sf http://localhost:8000/health && echo "Backend: OK" || echo "Backend: FAIL"

echo "=== Rollback Complete ==="
echo "If issues persist, contact: admin@verdischain.com" """,
             ["docker compose down", "docker compose up -d"],
             "Services restored to previous state",
             300, True),

            ("Health Check Script", ScriptType.HEALTH_CHECK.value, "health_check.sh",
             "Comprehensive health check for all services",
             """#!/bin/bash

echo "=== Verdis Ecosystem Health Check ==="
echo "Time: $(date)"
echo ""

# Check Docker services
echo "--- Docker Services ---"
docker compose -f /opt/verdis/Verdis/docker-compose.prod.yml ps

# Check Verdis Node
echo ""
echo "--- Verdis Node ---"
curl -sf http://localhost:9933/health 2>/dev/null && echo "Node: HEALTHY" || echo "Node: UNREACHABLE"
PEER_COUNT=$(curl -sf http://localhost:9933 -X POST -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","method":"system_peers","params":[],"id":1}' 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)['result']))" 2>/dev/null || echo "N/A")
echo "Peers: $PEER_COUNT"

# Check EvolvixOS Backend
echo ""
echo "--- EvolvixOS Backend ---"
curl -sf http://localhost:8000/health 2>/dev/null && echo "Backend: HEALTHY" || echo "Backend: UNREACHABLE"
curl -sf http://localhost:8000/health/detail 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20

# Check Frontend
echo ""
echo "--- Frontend ---"
curl -sf http://localhost:3000 2>/dev/null | head -1 && echo "Frontend: HEALTHY" || echo "Frontend: UNREACHABLE"

# Check Nginx
echo ""
echo "--- Nginx ---"
sudo nginx -t 2>&1
sudo systemctl status nginx --no-pager | head -5

# Check SSL
echo ""
echo "--- SSL ---"
echo | openssl s_client -connect verdischain.com:443 -servername verdischain.com 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "SSL: Check failed"

# Check Disk Space
echo ""
echo "--- Disk Space ---"
df -h / | head -2

# Check Memory
echo ""
echo "--- Memory ---"
free -h | head -2

echo ""
echo "=== Health Check Complete ===" """,
             ["curl -sf http://localhost:8000/health", "docker compose ps"],
             "All services healthy",
             60, False),
        ]

        for name, stype, filename, desc, content, commands, expected, timeout, root in scripts:
            sid = f"scr-{secrets.token_hex(8)}"
            self._scripts[sid] = DeployScript(
                id=sid, name=name, type=stype, filename=filename,
                description=desc, content=content, commands=commands,
                expected_output=expected, timeout=timeout,
                requires_root=root,
            )

    def _init_dns(self):
        """Initialize DNS records."""
        records = [
            ("A", "verdischain.com", "YOUR_SERVER_IP", "Main domain"),
            ("A", "www.verdischain.com", "YOUR_SERVER_IP", "WWW subdomain"),
            ("A", "api.verdischain.com", "YOUR_SERVER_IP", "API subdomain"),
            ("A", "explorer.verdischain.com", "YOUR_SERVER_IP", "Explorer subdomain"),
            ("A", "faucet.verdischain.com", "YOUR_SERVER_IP", "Faucet subdomain"),
            ("A", "ws.verdischain.com", "YOUR_SERVER_IP", "WebSocket subdomain"),
            ("CNAME", "rpc.verdischain.com", "verdischain.com", "RPC subdomain"),
            ("TXT", "verdischain.com", "v=spf1 include:_spf.verdischain.com ~all", "SPF record"),
            ("TXT", "_dmarc.verdischain.com", "v=DMARC1; p=quarantine; rua=mailto:admin@verdischain.com", "DMARC record"),
        ]
        for rtype, name, value, desc in records:
            rid = f"dns-{secrets.token_hex(8)}"
            self._dns_records[rid] = DNSRecord(
                id=rid, type=rtype, name=name, value=value, description=desc,
            )

    def _init_ssl(self):
        """Initialize SSL configurations."""
        domains = [
            "verdischain.com", "www.verdischain.com", "api.verdischain.com",
            "explorer.verdischain.com", "faucet.verdischain.com", "ws.verdischain.com",
        ]
        for domain in domains:
            sid = f"ssl-{secrets.token_hex(8)}"
            self._ssl_configs[sid] = SSLConfig(
                id=sid, domain=domain,
                cert_path=f"/etc/letsencrypt/live/{domain}/fullchain.pem",
                key_path=f"/etc/letsencrypt/live/{domain}/privkey.pem",
                commands=[
                    f"certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@verdischain.com --redirect",
                    f"openssl x509 -in /etc/letsencrypt/live/{domain}/fullchain.pem -noout -dates",
                ],
            )

    def _init_steps(self):
        """Initialize deployment steps."""
        steps = [
            (1, "Server Provisioning", "Provision Ubuntu 22.04+ server with 16GB RAM, 8 cores", "", "30 min", []),
            (2, "DNS Configuration", "Configure DNS records pointing to server IP", "bash setup_dns.sh", "10 min", [1]),
            (3, "Server Hardening", "Apply security hardening (firewall, SSH, fail2ban)", "bash harden_server.sh", "15 min", [1]),
            (4, "SSL Certificates", "Obtain Let's Encrypt SSL certificates", "bash setup_ssl.sh", "10 min", [2, 3]),
            (5, "Install Docker", "Install Docker and Docker Compose", "curl -fsSL get.docker.com | sh", "5 min", [3]),
            (6, "Clone Repository", "Clone Verdis repo to /opt/verdis", "git clone https://github.com/Protremix/Verdischain-.git", "2 min", [5]),
            (7, "Configure Environment", "Edit .env with production values", "nano .env", "5 min", [6]),
            (8, "Build Verdis Node", "Compile Verdis blockchain node", "cargo build --release", "20 min", [6]),
            (9, "Build Docker Images", "Build EvolvixOS backend and frontend images", "docker compose -f docker-compose.prod.yml build", "10 min", [5, 6]),
            (10, "Deploy Services", "Start all services with Docker Compose", "bash deploy.sh", "5 min", [7, 8, 9]),
            (11, "Configure Nginx", "Set up reverse proxy with SSL", "sudo cp nginx.conf /etc/nginx/ && sudo systemctl restart nginx", "5 min", [4, 10]),
            (12, "Setup Systemd", "Configure systemd services for auto-restart", "sudo systemctl enable verdis-node", "2 min", [10]),
            (13, "Health Checks", "Run comprehensive health check", "bash health_check.sh", "2 min", [10, 11]),
            (14, "Setup Monitoring", "Install Prometheus and Grafana", "bash setup_monitoring.sh", "15 min", [10]),
            (15, "Setup Backups", "Configure automated backups", "bash setup_backup.sh", "5 min", [10]),
            (16, "Final Verification", "Verify all endpoints over HTTPS", "curl -vI https://verdischain.com", "5 min", [11, 13]),
        ]
        for order, name, desc, cmd, est, deps in steps:
            sid = f"step-{secrets.token_hex(8)}"
            self._steps[sid] = DeploymentStep(
                id=sid, order=order, name=name, description=desc,
                command=cmd, expected_time=est, depends_on=deps,
            )

    # === Scripts ===

    def list_scripts(self, type: str = None, limit: int = 50) -> list[DeployScript]:
        scripts = list(self._scripts.values())
        if type:
            scripts = [s for s in scripts if s.type == type]
        scripts.sort(key=lambda s: s.name)
        return scripts[:limit]

    def get_script(self, script_id: str) -> Optional[DeployScript]:
        return self._scripts.get(script_id)

    def get_script_by_filename(self, filename: str) -> Optional[DeployScript]:
        for s in self._scripts.values():
            if s.filename == filename:
                return s
        return None

    def update_script_status(self, script_id: str, status: str) -> Optional[DeployScript]:
        script = self._scripts.get(script_id)
        if not script:
            return None
        script.status = status
        if status == ScriptStatus.COMPLETED.value:
            script.run_count += 1
        return script

    def generate_all_scripts(self) -> dict:
        """Generate all scripts as downloadable files."""
        result = {}
        for script in self._scripts.values():
            result[script.filename] = script.content
        return result

    # === DNS ===

    def list_dns_records(self, limit: int = 50) -> list[DNSRecord]:
        return list(self._dns_records.values())[:limit]

    def get_dns_record(self, record_id: str) -> Optional[DNSRecord]:
        return self._dns_records.get(record_id)

    # === SSL ===

    def list_ssl_configs(self, limit: int = 50) -> list[SSLConfig]:
        return list(self._ssl_configs.values())[:limit]

    def get_ssl_config(self, config_id: str) -> Optional[SSLConfig]:
        return self._ssl_configs.get(config_id)

    # === Steps ===

    def list_steps(self, limit: int = 50) -> list[DeploymentStep]:
        return sorted(self._steps.values(), key=lambda s: s.order)[:limit]

    def get_step(self, step_id: str) -> Optional[DeploymentStep]:
        return self._steps.get(step_id)

    def update_step_status(self, step_id: str, status: str) -> Optional[DeploymentStep]:
        step = self._steps.get(step_id)
        if not step:
            return None
        step.status = status
        return step

    def get_deployment_progress(self) -> dict:
        total = len(self._steps)
        completed = sum(1 for s in self._steps.values() if s.status == ScriptStatus.COMPLETED.value)
        pending = sum(1 for s in self._steps.values() if s.status == ScriptStatus.PENDING.value)
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "percentage": round(completed / max(1, total) * 100, 2),
            "next_step": next((s.to_dict() for s in self.list_steps() if s.status == ScriptStatus.PENDING.value), None),
        }

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "stats": {
                "total_scripts": len(self._scripts),
                "total_dns_records": len(self._dns_records),
                "total_ssl_configs": len(self._ssl_configs),
                "total_steps": len(self._steps),
                "completed_steps": sum(1 for s in self._steps.values() if s.status == ScriptStatus.COMPLETED.value),
                "pending_steps": sum(1 for s in self._steps.values() if s.status == ScriptStatus.PENDING.value),
            },
            "progress": self.get_deployment_progress(),
            "scripts": [s.to_dict() for s in self.list_scripts()],
            "dns_records": [r.to_dict() for r in self.list_dns_records()],
            "ssl_configs": [c.to_dict() for c in self.list_ssl_configs()],
            "steps": [s.to_dict() for s in self.list_steps()],
        }


_service: Optional[DeploymentPrepService] = None

def get_deployment_prep_service() -> DeploymentPrepService:
    global _service
    if _service is None:
        _service = DeploymentPrepService()
    return _service
