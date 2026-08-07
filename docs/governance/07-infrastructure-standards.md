# VERDIS GOVERNANCE DOCUMENT 07: INFRASTRUCTURE STANDARDS

**Document Reference:** VERDIS-GOV-07  
**Status:** PERMANENT GOVERNANCE STANDARD  
**Version:** 1.0.0  
**Ratified:** August 5, 2026  
**Scope:** Server Architecture, Docker Containers, Nginx Reverse Proxy, Systemd Services, Monitoring, Logging, Backups, and SSL across the Verdis Ecosystem.

---

## 1. OVERVIEW AND MANDATE

### 1.1 Purpose
This document establishes the official infrastructure standards for the Verdis Ecosystem. It governs physical and virtual server deployments, containerization rules, web server reverse proxy routing, service execution, real-time telemetry, logging protocols, backup schedules, and TLS/SSL security.

### 1.2 Scope
These infrastructure standards apply to all production environments, staging nodes, validator clusters, and cloud services supporting the seven core Verdis products:
1. **Verdis Chain** (Consensus Node, RPC Gateway, P2P Network)
2. **AegisOS Engine** (AI CTO, Orchestrator, Worker Pool)
3. **Verdis Applications** (Web Apps, Mobile Backends, API Endpoints)
4. **Verdis Trust Layer** (Identity Service, Cryptographic Signer)
5. **Verdis Developer Cloud** (Container Platform, RPC Hosting, CI/CD)
6. **Verdis Marketplace** (Registry, Extension Store)
7. **Verdis Developer Platform** (API Gateways, SDK Distribution)

---

## 2. SERVER ARCHITECTURE & OPERATING SYSTEM HARDENING

### 2.1 Current Physical Deployment Architecture (Single-Server Stage)
In the initial production phase, all core services are hosted on a single dedicated bare-metal server to maximize throughput and eliminate intra-service network latency:

- **Host IP Address**: `91.98.160.145`
- **Operating System**: Ubuntu 24.04 LTS (Long Term Support)
- **Kernel Version**: Linux 6.8+ (kernel optimized for high network I/O, `io_uring`, and eBPF)
- **Hardware Profile**: 64 CPU Cores, 256GB RAM, 4TB NVMe SSD (RAID 1), 10Gbps Uplink.

```
+-----------------------------------------------------------------------------------+
|  SINGLE SERVER HOST: 91.98.160.145 (Ubuntu 24.04 LTS)                            |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Nginx Reverse Proxy (Ports 80/443, SSL, TLS 1.3, Rate Limiting)             |  |
|  +-----------------------------------------------------------------------------+  |
|        |                  |                  |                  |                 |
|        v                  v                  v                  v                 |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
|  | Verdis    |      | AegisOS   |      | Web Apps  |      | Monitoring|           |
|  | Chain Node|      | Engine    |      | & APIs    |      | Prometheus|           |
|  | Port 9944 |      | Port 8000 |      | Port 3000 |      | Port 9090 |           |
|  +-----------+      +-----------+      +-----------+      +-----------+           |
+-----------------------------------------------------------------------------------+
```

### 2.2 Linux Kernel Sysctl Tuning Parameters (`/etc/sysctl.d/99-verdis-performance.conf`)
High-throughput blockchain nodes and API gateways require kernel-level networking and memory optimization:

```ini
# Maximum open file descriptors
fs.file-max = 2097152

# Network socket backlog and connection parameters
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# TCP Buffer tuning
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_max_syn_backlog = 3240000
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1

# Swap avoidance for high-memory server
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
```

### 2.3 UFW Firewall Configuration
Only ports required for public web traffic, SSH administration, and P2P gossip are exposed to the public interface `91.98.160.145`:

| Port | Protocol | Access Scope | Service Description |
| :--- | :--- | :--- | :--- |
| `22` | TCP | Restricted / SSH Keys | Secure Shell Administrative Access |
| `80` | TCP | Public World (`0.0.0.0/0`) | HTTP Ingress (Redirects to 443) |
| `443` | TCP | Public World (`0.0.0.0/0`) | HTTPS TLS 1.3 Ingress |
| `30333` | TCP / UDP | Public World (`0.0.0.0/0`) | Verdis Substrate P2P Node Gossip |
| `9944` | TCP | Localhost / Nginx Proxy | Substrate RPC / WebSocket Port (Internal) |
| `8000` | TCP | Localhost / Nginx Proxy | AegisOS AI Engine Port (Internal) |
| `9090` | TCP | Localhost / Nginx Proxy | Prometheus Monitoring (Internal) |

---

## 3. DOCKER & CONTAINERIZATION STANDARDS

All containerized applications in the Verdis Ecosystem must adhere strictly to these container standards to ensure security, determinism, and minimal image sizes.

### 3.1 Dockerfile Conventions
1. **Multi-Stage Builds**: Every Dockerfile must utilize multi-stage builds (`builder` stage for compilation, `runner` stage for runtime).
2. **Base Images**: Use official, minimal base images (e.g., `debian:bookworm-slim`, `alpine:3.20`, or `gcr.io/distroless`).
3. **Non-Root User Execution**: Running containers as `root` (UID 0) is strictly forbidden. Containers must create and run as unprivileged user `verdis` (UID 10001, GID 10001).
4. **Explicit Image Tagging**: Never use `latest` tags. Always pin specific base image digests or explicit version tags (e.g., `alpine:3.20.2`).
5. **Clean Up Layer Artifacts**: Remove apt caches, cargo target build caches, or temporary npm files in the same `RUN` layer using `apt-get clean`.

### 3.2 Canonical Production Dockerfile (Rust / Chain Node Example)

```dockerfile
# Stage 1: Build Environment
FROM rust:1.80-slim-bookworm AS builder
WORKDIR /usr/src/verdis

# Install build dependencies
RUN apt-get update && apt-get install -y     pkg-config     libssl-dev     git     clang     cmake     && apt-get clean

# Copy dependency manifests and source code
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Build release binary deterministically
RUN cargo build --release --bin verdis-node

# Stage 2: Minimal Runtime Environment
FROM debian:bookworm-slim AS runner

# Create non-root verdis user and group
RUN groupadd -g 10001 verdis &&     useradd -u 10001 -g verdis -m -s /bin/false verdis

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y     ca-certificates     libssl3     curl     && apt-get clean

WORKDIR /app

# Copy compiled binary from builder
COPY --from=builder /usr/src/verdis/target/release/verdis-node /app/verdis-node
RUN chown -R verdis:verdis /app

USER verdis:verdis

# Health Check Definition
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3   CMD curl -f http://localhost:9933/health || exit 1

EXPOSE 9944 9933 30333

ENTRYPOINT ["/app/verdis-node"]
CMD ["--chain=mainnet", "--rpc-external", "--rpc-cors=all"]
```

### 3.3 Docker Compose Orchestration Structure

```yaml
version: '3.8'

services:
  verdis-chain:
    image: verdis/chain-node:1.2.0
    container_name: verdis-chain-production
    restart: always
    user: "10001:10001"
    ports:
      - "127.0.0.1:9944:9944"
      - "127.0.0.1:9933:9933"
      - "30333:30333"
    volumes:
      - /var/lib/verdis/chain-data:/app/data
    environment:
      - RUST_LOG=info,verdis=debug
    deploy:
      resources:
        limits:
          cpus: '16.0'
          memory: 32G
        reservations:
          cpus: '4.0'
          memory: 8G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9933/health"]
      interval: 15s
      timeout: 3s
      retries: 3
```

---

## 4. NGINX REVERSE PROXY & 12 SUBDOMAIN ROUTING

Nginx serves as the single public entry point on host `91.98.160.145`, handling SSL termination, rate limiting, and HTTP-to-HTTPS redirection across all 12 official Verdis subdomains.

### 4.1 Subdomain Mapping & Upstream Matrix
| Subdomain | Public Domain | Target Upstream Port | Core Product Service |
| :--- | :--- | :--- | :--- |
| **Main Portal** | `verdis.network` | `localhost:3000` | Verdis Landing Page & Product Hub |
| **Explorer** | `explorer.verdis.network` | `localhost:3001` | Solscan-inspired Blockchain Explorer |
| **RPC Gateway** | `rpc.verdis.network` | `localhost:9944` | Chain WebSocket / HTTP RPC Node |
| **AegisOS Engine** | `aegis.verdis.network` | `localhost:8000` | AegisOS AI Engineering Portal |
| **Web Wallet** | `wallet.verdis.network` | `localhost:3002` | Verdis Non-Custodial Web Wallet |
| **Dev Cloud** | `cloud.verdis.network` | `localhost:8080` | Verdis Developer Cloud Console |
| **Marketplace** | `marketplace.verdis.network`| `localhost:3003` | Verdis Extension & Plugin Store |
| **Documentation** | `docs.verdis.network` | `localhost:3004` | Technical Docs & Whitepaper Portal |
| **API Gateway** | `api.verdis.network` | `localhost:8081` | Core REST & GraphQL API Gateway |
| **Trust Identity** | `id.verdis.network` | `localhost:8082` | Verdis ID Verification & Auth |
| **Monitoring** | `monitor.verdis.network` | `localhost:3005` | Grafana Telemetry Dashboards |
| **Dev Portal** | `dev.verdis.network` | `localhost:3006` | Developer Sandbox & Playground |

### 4.2 Security Headers & Rate Limiting Rules
All Nginx server blocks must enforce standard high-security headers and rate limits:

```nginx
# Security Header Includes (/etc/nginx/conf.d/security_headers.conf)
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' wss://rpc.verdis.network https://rpc.verdis.network;" always;

# Rate Limiting Zones (/etc/nginx/nginx.conf)
limit_req_zone $binary_remote_addr zone=rpc_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=50r/s;
```

### 4.3 Canonical Subdomain Nginx Server Block (RPC Gateway Example)

```nginx
# /etc/nginx/sites-available/rpc.verdis.network.conf
server {
    listen 80;
    server_name rpc.verdis.network;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name rpc.verdis.network;

    ssl_certificate /etc/letsencrypt/live/rpc.verdis.network/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rpc.verdis.network/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    include /etc/nginx/conf.d/security_headers.conf;

    # WebSocket & HTTP RPC Proxying
    location / {
        limit_req zone=rpc_limit burst=20 nodelay;

        proxy_pass http://127.0.0.1:9944;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket Timeout Tuning
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
    }
}
```

---

## 5. SYSTEMD SERVICE STANDARDS

For native Linux host services running outside Docker containers, systemd service units must follow strict isolation and restart policies.

### 5.1 Service Unit Requirements
1. **Automatic Restart**: `Restart=always` with `RestartSec=5s`.
2. **File Descriptor Limits**: `LimitNOFILE=65536` to prevent socket starvation under high network load.
3. **Process Sandboxing**: `ProtectSystem=full`, `PrivateTmp=true`, `ProtectHome=true`, `NoNewPrivileges=true`.
4. **Environment Isolation**: Load environment variables from restricted configuration files (`/etc/verdis/env.conf`, `chmod 600`).

### 5.2 Canonical Systemd Unit File (`verdis-chain.service`)

```ini
[Unit]
Description=Verdis Layer-1 Blockchain Node
After=network-online.target local-fs.target
Wants=network-online.target

[Service]
Type=simple
User=verdis
Group=verdis
WorkingDirectory=/var/lib/verdis
ExecStart=/usr/local/bin/verdis-node     --chain=/etc/verdis/mainnet-spec.json     --base-path=/var/lib/verdis/data     --rpc-port=9944     --port=30333     --validator     --name="Verdis-Primary-Node"

Restart=always
RestartSec=5s
LimitNOFILE=65536
MemoryMax=32G
CPUQuota=1600%

# Security & Isolation Hardening
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
NoNewPrivileges=true
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
```

---

## 6. AUTOMATED DEPLOYMENT & ZERO-DOWNTIME STRATEGY

Deployment to production host `91.98.160.145` is automated through SSH key authentication and continuous deployment scripts.

### 6.1 Deployment Pipeline Flow
1. **GitHub Actions / CI Runner**: Compiles binary/container and runs 100% of tests.
2. **SSH Connection**: Authenticates using encrypted SSH key (`verdis-deploy-key`).
3. **Artifact Transfer**: Atomic transfer of release binaries to `/opt/verdis/releases/vX.Y.Z/`.
4. **Symlink Swap**: Atomic update of `/opt/verdis/current` symlink.
5. **Service Reload**: Execute `systemctl reload verdis-*.service` or Nginx upstream reload (`nginx -s reload`).
6. **Health Verification**: Query `/health` endpoint on target port; if unhealthy, revert symlink automatically within 10 seconds.

---

## 7. TELEMETRY, MONITORING & OBSERVABILITY

System metrics are collected continuously using Prometheus and visualized via Grafana.

### 7.1 Prometheus Monitoring Stack (21 Telemetry Targets)
The Prometheus instance monitors 21 explicit targets across infrastructure and application layers:

1. **Host Linux System** (`Node Exporter` - Port 9100)
2. **Nginx Reverse Proxy** (`Nginx Exporter` - Port 9113)
3. **Docker Engine Metrics** (Port 9323)
4. **Verdis Consensus Engine** (Port 9615)
5. **Verdis RPC Gateway** (Port 9616)
6. **Verdis Transaction Mempool** (Port 9617)
7. **Verdis Substrate Runtime State** (Port 9618)
8. **AegisOS AI Orchestration Engine** (Port 8000/metrics)
9. **AegisOS Agent Execution Workers** (Port 8001/metrics)
10. **Verdis Web Wallet Backend** (Port 3002/metrics)
11. **Verdis Explorer Backend API** (Port 3001/metrics)
12. **Verdis Trust Identity Service** (Port 8082/metrics)
13. **Verdis Developer Cloud Controller** (Port 8080/metrics)
14. **Verdis Marketplace Registry** (Port 3003/metrics)
15. **Verdis Documentation Server** (Port 3004/metrics)
16. **PostgreSQL Database Exporter** (Port 9187)
17. **SQLite DB Metrics Service** (Port 9188)
18. **Redis / Key-Value Cache Exporter** (Port 9121)
19. **Certbot SSL Expiration Exporter** (Port 9099)
20. **Systemd Unit Status Monitor** (Port 9558)
21. **Backup Cron Job Status Exporter** (Port 9101)

### 7.2 Prometheus Scrape Configuration (`/etc/prometheus/prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/alert_rules.yml"

scrape_configs:
  - job_name: 'node_exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'verdis_consensus'
    static_configs:
      - targets: ['localhost:9615']

  - job_name: 'verdis_rpc'
    static_configs:
      - targets: ['localhost:9616']

  - job_name: 'aegisos_engine'
    static_configs:
      - targets: ['localhost:8000']
```

### 7.3 Critical Prometheus Alert Rules (`/etc/prometheus/alert_rules.yml`)

```yaml
groups:
  - name: verdis_infrastructure_alerts
    rules:
      - alert: HostHighCpuUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Host CPU utilization above 85% on {{ $labels.instance }}"

      - alert: HostHighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Host RAM utilization above 90%"

      - alert: VerdisBlockProductionHalted
        expr: increase(verdis_blocks_produced_total[3m]) == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Chain block production halted for > 2 minutes!"

      - alert: SslCertificateExpiringSoon
        expr: (certexporter_certificate_expires_in_seconds / 86400) < 15
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "SSL Certificate for {{ $labels.domain }} expires in less than 15 days"
```

---

## 8. STRUCTURED LOGGING & LOGROTATE STANDARDS

### 8.1 JSON Structured Log Format
All application logs across all 7 products must output structured JSON to `stdout`/`stderr` adhering to this exact schema:

```json
{
  "timestamp": "2026-08-05T09:28:00.123Z",
  "level": "INFO",
  "service": "verdis-rpc-gateway",
  "trace_id": "c7a91b40-9e23-4211-b841-82ff3023a101",
  "module": "rpc::websocket",
  "message": "Processed author_submitExtrinsic",
  "context": {
    "tx_hash": "0x7d9f2a...",
    "sender": "5GrwvaEF...",
    "duration_ms": 1.45
  }
}
```

### 8.2 Logrotate Configuration (`/etc/logrotate.d/verdis`)

```
/var/log/verdis/*.log {
    daily
    rotate 14
    missingok
    notifempty
    compress
    delaycompress
    maxsize 100M
    sharedscripts
    postrotate
        systemctl reload verdis-*.service > /dev/null 2>&1 || true
        /usr/bin/pkill -HUP nginx > /dev/null 2>&1 || true
    endscript
}
```

---

## 9. AUTOMATED DAILY BACKUP & DISASTER RECOVERY

Chain state databases, AegisOS project stores, and system configurations are backed up daily.

### 9.1 Backup Schedule & Retention Policy
- **Execution Time**: Daily at 02:00 UTC via systemd timer / crontab (`0 2 * * *`).
- **Retention Period**: 30 days locally, 90 days offsite.
- **Encryption**: AES-256 GPG encryption prior to offsite sync.

### 9.2 Automated Backup Shell Script (`/usr/local/bin/verdis-backup.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/verdis/${BACKUP_DATE}"
LOG_FILE="/var/log/verdis/backup.log"

mkdir -p "${BACKUP_DIR}"
echo "[${BACKUP_DATE}] Starting Verdis daily backup..." >> "${LOG_FILE}"

# 1. Backup Chain State Snapshot
echo "Backing up chain state..." >> "${LOG_FILE}"
tar -czf "${BACKUP_DIR}/chain_state.tar.gz" -C /var/lib/verdis/data db

# 2. Backup AegisOS Databases & Project Repositories
echo "Backing up AegisOS state..." >> "${LOG_FILE}"
pg_dump -U verdis aegisos_db | gzip > "${BACKUP_DIR}/aegisos_postgres.sql.gz"
tar -czf "${BACKUP_DIR}/aegisos_projects.tar.gz" -C /var/lib/aegisos projects

# 3. Backup Nginx & System Configurations
tar -czf "${BACKUP_DIR}/system_config.tar.gz" /etc/nginx /etc/systemd/system/verdis* /etc/verdis

# 4. Prune Backups Older Than 30 Days
find /var/backups/verdis/ -mindepth 1 -maxdepth 1 -type d -mtime +30 -delete

echo "[${BACKUP_DATE}] Backup completed successfully." >> "${LOG_FILE}"
```

### 9.3 Bare-Metal Disaster Recovery Procedure
In the event of total server hardware failure on `91.98.160.145`:

1. Provision fresh Ubuntu 24.04 LTS instance with IP `91.98.160.145`.
2. Execute system bootstrapping script (`/opt/verdis/ci-cd/bootstrap.sh`).
3. Restore system configuration from latest GPG-encrypted offsite backup archive (`system_config.tar.gz`).
4. Re-install Certbot SSL keys to `/etc/letsencrypt/`.
5. Restore PostgreSQL and SQLite databases from `aegisos_postgres.sql.gz`.
6. Restore chain state database `chain_state.tar.gz` to `/var/lib/verdis/data`.
7. Start systemd services via `systemctl start verdis-chain verdis-aegisos nginx`.
8. Run smoke tests across all 12 subdomains via `curl -f https://*.verdis.network/health`.

---

## 10. SSL / TLS AUTOMATION VIA CERTBOT

All 12 subdomains are secured via Let's Encrypt TLS 1.3 certificates.

- **Auto-Renewal Timer**: Managed via `certbot.timer` running twice daily.
- **Reload Hook**: Post-renewal hook triggers `nginx -t && systemctl reload nginx`.
- **Validation**: DNS-01 or HTTP-01 challenge automated via Certbot.

---

## 11. INFRASTRUCTURE AUDIT CHECKLIST

Before any production release or infrastructure configuration change, the following checklist must be satisfied:

- [ ] **Host IP Binding**: Backend services bind strictly to `127.0.0.1` or internal Docker networks; only Nginx binds to public interface `91.98.160.145`.
- [ ] **Non-Root Execution**: Containers and systemd services execute under user `verdis` (UID 10001).
- [ ] **Kernel Sysctl Applied**: Network high-throughput tuning active in `/etc/sysctl.d/99-verdis-performance.conf`.
- [ ] **SSL Configuration**: Valid Let's Encrypt SSL active on all 12 subdomains with TLS 1.3 enabled.
- [ ] **Rate Limits Active**: Nginx rate limit zones (`rpc_limit`, `api_limit`) enabled and verified.
- [ ] **Monitoring Telemetry**: Target verified active in Prometheus targets dashboard (`monitor.verdis.network`).
- [ ] **Structured Logging**: Application logs outputting valid JSON to `stdout`.
- [ ] **Backup Verification**: Daily 2am cron script verified and test restoration run completed.
- [ ] **Disaster Recovery Tested**: Bare-metal recovery playbook tested and validated.
- [ ] **GPT-4o Review**: Infrastructure configuration reviewed and approved by GPT-4o CTO quality gate.
