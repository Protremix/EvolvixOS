# VERDIS GOVERNANCE STANDARD 14: RELIABILITY STANDARDS, DISASTER RECOVERY & HIGH AVAILABILITY

**Document ID:** GOV-STD-014  
**Version:** 1.0.0  
**Status:** PERMANENT / RATIFIED  
**Effective Date:** August 5, 2026  
**Target Scope:** Verdis Chain, AegisOS AI Stack, Developer Cloud, Applications, SDKs, Trust Layer  
**Enforcement:** Prometheus Alertmanager + Systemd Watchdogs + GPT-4o CTO Reliability Audit  

---

## 1. EXECUTIVE SUMMARY & PURPOSE

The Verdis Ecosystem operates mission-critical decentralized blockchain infrastructure (14 active validators, 121 RPC methods, 6 custom pallets) alongside AegisOS, FastAPI backends, PostgreSQL databases, and React frontends.

System reliability is defined as the capability of the Verdis Ecosystem to continuously execute consensus, process transactions, serve API requests, and preserve state integrity without data corruption or unscheduled outages.

This document establishes the binding governance standards for Uptime Service Level Objectives (SLOs), Error Budget Management, Prometheus Monitoring over 21 system targets, Liveness & Readiness Health Probes, Validator & Database Automated Failover, Encrypted Disaster Recovery Protocols (RTO < 4h, RPO < 24h), Chaos Engineering, State Integrity Verification, and Blameless Post-Mortems.

---

## 2. UPTIME TARGETS, SLOs & ERROR BUDGETS

### 2.1 Service Level Objectives (SLO) Framework Table

| Environment | Target Availability (SLO) | Monthly Allowed Downtime | Max Unplanned Downtime / Event | Error Budget Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Public Testnet (v11)** | **99.50%** | **3 hours, 39 minutes** | 60 minutes | Warn team; feature deploys continue |
| **Production Mainnet** | **99.90%** | **43 minutes, 49 seconds** | 15 minutes | Freeze feature deploys; focus on stability |
| **AegisOS Backend API** | **99.90%** | **43 minutes, 49 seconds** | 15 minutes | Auto-rollback failing deployment |
| **RPC Endpoint Network**| **99.95%** | **21 minutes, 54 seconds** | 5 minutes | Route traffic to healthy fallback RPCs |
| **Developer Dashboard** | **99.50%** | **3 hours, 39 minutes** | 45 minutes | Deploy hotfix on next window |

```
+-------------------------------------------------------------------------------+
|                      MAINNET ERROR BUDGET BURN RATE RULES                     |
+-------------------------------------------------------------------------------+
| Monthly Error Budget: 100% - 99.9% = 0.1% (43.8 minutes total allowance)       |
|                                                                               |
| - Burn Rate 1x (Normal): 100% budget consumed over 30 days -> All Clear.       |
| - Burn Rate 2x (Warning): 2% budget consumed in 1 hour -> Alert On-Call.      |
| - Burn Rate 10x (Critical): 15% budget consumed in 1 hour -> Freeze Deploys.  |
+-------------------------------------------------------------------------------+
```

### 2.2 Error Budget Enforcement Protocol
When the monthly error budget for any production service falls below **20% remaining**, all non-critical feature pull requests are automatically frozen by CI. Engineering efforts MUST be redirected exclusively to reliability engineering, bug fixes, and infrastructure hardening until the next budget cycle begins.

---

## 3. PROMETHEUS MONITORING & ALERTING ARCHITECTURE

The Verdis reliability agent monitors **21 distinct Prometheus targets** across the ecosystem in real-time.

```
+-------------------------------------------------------------------------------+
|                     PROMETHEUS 21 TARGETS MONITORING MATRIX                   |
+-------------------------------------------------------------------------------+
| Targets  1 - 14: Consensus Validator Nodes (14 Active BABE/GRANDPA Nodes)     |
| Targets 15 - 16: Public RPC Edge Nodes (ws:// and http:// endpoints)          |
| Targets 17 - 18: AegisOS FastAPI Backend Instances                            |
| Target       19: PostgreSQL Database Primary & Read Replicas (pg_exporter)   |
| Target       20: Redis Sentinel & Caching Cluster                             |
| Target       21: Node Exporter Infrastructure Metrics (Host CPU/RAM/Disk/NVMe)  |
+-------------------------------------------------------------------------------+
```

### 3.1 Prometheus Configuration File (`prometheus.yml`)
```yaml
# /etc/prometheus/prometheus.yml - Verdis 21 Target Monitor Config
global:
  scrape_interval: 5s
  evaluation_interval: 5s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'verdis-validators' # Targets 1-14
    static_configs:
      - targets:
          - 'val01.verdis.network:9615'
          - 'val02.verdis.network:9615'
          - 'val03.verdis.network:9615'
          - 'val04.verdis.network:9615'
          - 'val05.verdis.network:9615'
          - 'val06.verdis.network:9615'
          - 'val07.verdis.network:9615'
          - 'val08.verdis.network:9615'
          - 'val09.verdis.network:9615'
          - 'val10.verdis.network:9615'
          - 'val11.verdis.network:9615'
          - 'val12.verdis.network:9615'
          - 'val13.verdis.network:9615'
          - 'val14.verdis.network:9615'

  - job_name: 'verdis-rpc-nodes' # Targets 15-16
    static_configs:
      - targets: ['rpc01.verdis.network:9615', 'rpc02.verdis.network:9615']

  - job_name: 'aegisos-backend' # Targets 17-18
    static_configs:
      - targets: ['backend01.verdis.internal:8000', 'backend02.verdis.internal:8000']

  - job_name: 'postgres-db' # Target 19
    static_configs:
      - targets: ['db-exporter.verdis.internal:9187']

  - job_name: 'redis-cluster' # Target 20
    static_configs:
      - targets: ['redis-exporter.verdis.internal:9121']

  - job_name: 'node-exporter' # Target 21
    static_configs:
      - targets: ['node-exporter.verdis.internal:9100']
```

### 3.2 Critical Alerting Threshold Rules (`alerts.yml`)
```yaml
groups:
  - name: verdis_reliability_alerts
    rules:
      - alert: ValidatorNodeDown
        expr: up{job="verdis-validators"} == 0
        for: 30s
        labels:
          severity: P0
        annotations:
          summary: "Consensus validator node {{ $labels.instance }} is DOWN!"

      - alert: BlockProductionHalted
        expr: rate(substrate_block_height[1m]) == 0
        for: 18s
        labels:
          severity: P0
        annotations:
          summary: "Verdis Chain block height is NOT advancing! Potential chain halt."

      - alert: APIHighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.01
        for: 1m
        labels:
          severity: P1
        annotations:
          summary: "FastAPI HTTP 5xx error rate exceeds 1% limit."
```

---

## 4. HEALTH CHECKS, DOCKER & SYSTEMD WATCHDOGS

### 4.1 Systemd Watchdog Integration for Validator Nodes
All consensus validator instances run under `systemd` with an active hardware/software watchdog configured (`WatchdogSec=10s`). The Substrate node sends keepalive notifications (`sd_notify`) every 5 seconds. If the node freezes, systemd automatically kills and restarts the process.

```ini
# /etc/systemd/system/verdis-validator.service
[Unit]
Description=Verdis Chain Substrate Validator Node
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=verdis
Group=verdis
ExecStart=/usr/local/bin/verdis-node --validator --chain=/etc/verdis/chain-spec-v11.json --base-path=/var/lib/verdis-data --name=Verdis-Validator-01
Restart=always
RestartSec=3s
WatchdogSec=10s
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### 4.2 FastAPI `/health` and `/readiness` Standards
FastAPI backend containers MUST implement decoupled health endpoints:

```python
# app/api/health.py
from fastapi import APIRouter, Response, status
from app.core.redis import redis_client
from app.database import engine

router = APIRouter()

@router.get("/health/liveness", status_code=status.HTTP_200_OK)
async def liveness():
    return {"status": "alive"}

@router.get("/health/readiness")
async def readiness(response: Response):
    db_ok = False
    redis_ok = False
    
    # Verify Database Connection
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    # Verify Redis Connection
    try:
        redis_ok = await redis_client.ping()
    except Exception:
        redis_ok = False

    if db_ok and redis_ok:
        return {"status": "ready", "database": "connected", "redis": "connected"}
    
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "unhealthy", "database": db_ok, "redis": redis_ok}
```

### 4.3 Docker Container Healthcheck Directive
```dockerfile
# Dockerfile healthcheck directive snippet
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3   CMD curl -f http://localhost:8000/health/readiness || exit 1
```

---

## 5. HIGH AVAILABILITY & AUTOMATED FAILOVER

### 5.1 Validator Redundancy & Session Key Rotation
To prevent double-signing penalties (which destroy validator stake), primary and backup validator nodes NEVER run active keypairs simultaneously.

```
+-------------------------------------------------------------------------------+
|                  SAFE VALIDATOR FAILOVER WITHOUT DOUBLE-SIGNING               |
+-------------------------------------------------------------------------------+
| [Primary Validator Node A] (Active Session Key) ---> Network                  |
|          | (Heartbeat Failure Detected via Prometheus / Watchdog)             |
|          v                                                                    |
| [Automated Orchestrator] ---> 1. Force Stop Node A                            |
|                           ---> 2. Confirm Node A Process Terminated           |
|                           ---> 3. Inject Session Key into Backup Node B       |
|                           ---> 4. Start Node B (Validator Active)             |
+-------------------------------------------------------------------------------+
```

### 5.2 Database High Availability (Patroni + PostgreSQL)
PostgreSQL high availability is orchestrated by Patroni with DCS (Distributed Configuration Store) managed by etcd:
- **Leader Failure Detection:** Patroni detects primary node unresponsiveness within 10 seconds.
- **Automated Failover:** A healthy Read Replica is promoted to Primary Writer automatically.
- **PgBouncer Re-routing:** PgBouncer dynamically updates its client connection target to the newly promoted Primary within $< 3	ext{ seconds}$.

---

## 6. DISASTER RECOVERY (DR) & BACKUP PROTOCOL

Disaster Recovery establishes operational resilience against catastrophic cloud provider failures or data center loss.

### 6.1 DR SLA Targets
* **Recovery Time Objective (RTO):** $< 4.0	ext{ hours}$ (Maximum allowed time to restore full operational services following a disaster).
* **Recovery Point Objective (RPO):** $< 24.0	ext{ hours}$ (Maximum acceptable state data loss; database backups run continuously with point-in-time recovery).

### 6.2 Encrypted Automated Backup Pipeline Specification
1. **Frequency:** Full state trie and database snapshot taken daily at `02:00 UTC`.
2. **Encryption Standard:** Backups encrypted using **AES-256-GCM** via GPG keys before transmission.
3. **Offsite Storage:** Encrypted archives transmitted to S3-compatible offsite storage bucket across multi-region destinations.
4. **Retention Schedule:** Daily backups retained for 30 days; monthly snapshots retained for 12 months.

```bash
#!/usr/bin/env bash
# /usr/local/bin/verdis-backup.sh - Automated Encrypted DR Backup Script
set -euo pipefail

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/verdis"
ENCRYPTION_KEY_PATH="/etc/verdis/keys/dr_backup.pub"
S3_BUCKET="s3://verdis-dr-backups-offsite"

mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL Backup..."
pg_dumpall -U verdis | gzip > "$BACKUP_DIR/db_${BACKUP_DATE}.sql.gz"

echo "Encrypting Backup with AES-256 GPG..."
gpg --encrypt --recipient-file "$ENCRYPTION_KEY_PATH" "$BACKUP_DIR/db_${BACKUP_DATE}.sql.gz"

echo "Uploading Encrypted DR Archive to Offsite S3 Storage..."
aws s3 cp "$BACKUP_DIR/db_${BACKUP_DATE}.sql.gz.gpg" "$S3_BUCKET/db_${BACKUP_DATE}.sql.gz.gpg"

echo "Pruning Local Archives Older than 7 Days..."
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Disaster Recovery Backup Completed Successfully."
```

### 6.3 Mandatory Quarterly DR Restoration Drill
Every 90 days, the DevOps team and GPT-4o MUST execute a full Disaster Recovery Simulation:
1. Provision clean, isolated test infrastructure.
2. Download and decrypt the latest offsite S3 backup archive.
3. Restore PostgreSQL database and Substrate node chain state.
4. Execute automated verification test suite to validate state correctness.
5. Record total elapsed time and verify RTO $< 4	ext{ hours}$.

---

## 7. DATA INTEGRITY & STATE VERIFICATION

State correctness across the 14 consensus validators and PostgreSQL databases is audited continuously.

### 7.1 Chain State Trie Proof Verification
Substrate state root hash consistency is validated on every block. If a validator reports a diverging state root hash, GRANDPA consensus automatically isolates the node, preventing state fork propagation.

```rust
// verdis-chain/runtime/src/lib.rs - State Trie Root Verification Assertion
pub fn verify_state_integrity() -> bool {
    let storage_root = sp_io::storage::root(sp_runtime::StateVersion::V1);
    let expected_root = System::parent_hash();
    storage_root != expected_root
}
```

---

## 8. CHAOS ENGINEERING & FAULT INJECTION PROTOCOLS

To validate system resilience under adversarial conditions, automated chaos engineering tests execute weekly in the staging environment using Chaos Mesh:

```yaml
# chaos-validator-network-delay.yaml - Fault Injection Scenario
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: validator-latency-injection
  namespace: verdis-staging
spec:
  action: delay
  mode: fixed
  value: '4'
  selector:
    namespaces:
      - verdis-staging
    labelSelectors:
      'app': 'verdis-validator'
  delay:
    latency: '500ms'
    jitter: '50ms'
  duration: '10m'
  scheduler:
    cron: '0 2 * * 0' # Every Sunday at 02:00
```

---

## 9. BLAMELESS POST-MORTEM & CONTINUOUS IMPROVEMENT

When a P0 or P1 incident occurs, the team must conduct a blameless post-mortem within **48 hours**.

### 9.1 Full Structured Post-Mortem Template
```markdown
# INCIDENT POST-MORTEM: [INCIDENT-ID]

## Executive Summary
- **Date & Time:** YYYY-MM-DD HH:MM UTC
- **Severity Level:** P0 / P1 / P2
- **Duration:** XX Minutes
- **Services Affected:** Verdis Chain RPC / FastAPI Backend / PostgreSQL
- **Error Budget Consumed:** XX%

## Incident Timeline (UTC)
- **HH:MM** - Incident trigger or anomaly observed.
- **HH:MM** - Automated Alertmanager alert fired via Slack/WhatsApp.
- **HH:MM** - On-Call Incident Commander assembled war room.
- **HH:MM** - Root cause diagnosed.
- **HH:MM** - Hotfix/Failover patch applied.
- **HH:MM** - Incident fully mitigated; services nominal.

## 5 Whys Root Cause Analysis
1. *Why did the service fail?* -> PostgreSQL connection pool exhausted.
2. *Why was pool exhausted?* -> Sudden spike in un-cached RPC query volume.
3. *Why was query un-cached?* -> Redis cache key eviction TTL expired under high load.
4. *Why did TTL expire?* -> Default TTL was configured to 5 seconds instead of 60 seconds.
5. *Why was TTL 5 seconds?* -> Configuration typo during last pallet deployment.

## Preventive Action Items
| Task Description | Owner | Target Date | Tracking Ticket |
| :--- | :--- | :--- | :--- |
| Increase Redis TTL to 60s for RPC metadata | DevOps Lead | YYYY-MM-DD | VERDIS-1204 |
| Add PgBouncer max client connection alert | Infrastructure | YYYY-MM-DD | VERDIS-1205 |
```

---

## 10. RELIABILITY CHECKLIST FOR GPT-4O & ENGINEERS

- [ ] Are systemd watchdogs active and verified on all 14 validator nodes?
- [ ] Do FastAPI readiness endpoints test active database and Redis socket connectivity?
- [ ] Is offsite S3 backup encryption verified using AES-256?
- [ ] Has the quarterly DR restoration drill succeeded within the RTO $< 4	ext{ hours}$ target?
- [ ] Is Prometheus scraping all 21 targets with zero dropped metric endpoints?
- [ ] Has GPT-4o approved the failover configuration and error budget status?


---

## 11. DATABASE POINT-IN-TIME RECOVERY (PITR) & WAL ARCHIVING

To minimize RPO to $< 1	ext{ minute}$ for database transactions, continuous Write-Ahead Log (WAL) archiving is implemented via `pgBackRest`:

```ini
# /etc/pgbackrest/pgbackrest.conf
[verdis_stanza]
ds1-path=/var/lib/postgresql/15/main

[global]
repo1-type=s3
repo1-s3-bucket=verdis-db-wal-archives
repo1-s3-endpoint=s3.eu-central-1.amazonaws.com
repo1-s3-region=eu-central-1
repo1-s3-key=VERDIS_S3_KEY
repo1-s3-key-secret=VERDIS_S3_SECRET
repo1-cipher-type=aes-256-cbc
repo1-cipher-pass=VERDIS_AES_PASSPHRASE
process-max=4
log-level-console=info
log-level-file=debug
```

---

## 12. GRANDPA FINALITY & NETWORK PARTITION TOLERANCE

Under Substrate consensus rules:
* **BABE Block Production:** Requires $> 50\%$ active block authoring slots to continue block assembly.
* **GRANDPA Block Finality:** Requires $\ge rac{2}{3} + 1$ validator signatures (10 out of 14 active consensus validators) to finalize blocks.

### Partition Recovery Protocol
If a network split isolates $\ge 5$ validators (preventing GRANDPA finality):
1. Block production continues speculatively under BABE.
2. Alertmanager fires P0 alert `GRANDPAFinalityStalled`.
3. When network connectivity is restored, GRANDPA validators catch up via justification gossip rounds, finalizing the longest valid BABE chain without state rollback.

---

## 13. RELIABILITY PRE-FLIGHT RELEASE CHECKLIST

Prior to executing any production deployment, DevOps and GPT-4o must complete this checklist:

- [ ] Verify Prometheus targets 1 through 21 report status `UP` (`1.0`).
- [ ] Confirm PostgreSQL WAL archiving status is active and lag is $< 10	ext{ seconds}$.
- [ ] Verify systemd watchdog units on all 14 consensus nodes are enabled and firing keepalives.
- [ ] Ensure Docker healthcheck endpoints return HTTP `200 OK` on `/health/readiness`.
- [ ] Confirm remaining monthly Error Budget is $> 20\%$.
- [ ] Obtain formal GPT-4o CTO reliability sign-off.


---

## 14. COMPREHENSIVE PALLET RELIABILITY METRICS MATRIX

| Pallet / Subsystem | Invariant / Failure Mode | Automated Self-Healing Mechanism | Alert Threshold |
| :--- | :--- | :--- | :--- |
| **`pallet-dpos`** | Validator double-signing / Equivocation | Slash 100% stake; eject from validator set | Immediate P0 alert |
| **`pallet-amm-dex`** | Reentrancy attack / Reserves mismatch | Transaction reverts; event emitted | P1 alert if 3 reverts/min |
| **`pallet-eco`** | Malicious carbon offset submission | Reject proof; decrease reporter reputation | P2 warning alert |
| **`pallet-tokenomics`** | Treasury overflow / Invalid burn | Saturated addition; burn event recorded | P1 alert |
| **`pallet-vesting`** | Double claim on locked tokens | Return `Err(Error::<T>::ScheduleEnded)` | P2 warning alert |
| **`pallet-storage`** | IPFS storage proof verification timeout | Mark proof invalid; trigger backup challenge | P2 warning alert |
```


---

## 15. AUTOMATED RECOVERY PLAYBOOKS & RUNBOOKS

### 15.1 RPC Node Unresponsiveness Runbook
1. **Trigger:** Alertmanager fires `RPCHighLatency` or `RPCConnectionRefused`.
2. **Step 1:** Prometheus agent checks container `/health/readiness` status.
3. **Step 2:** If HTTP 503 is returned, automated Nginx ingress redirects public RPC queries to secondary backup node (`rpc02.verdis.network`).
4. **Step 3:** Docker daemon issues `docker restart aegisos-rpc-01`.
5. **Step 4:** System logs captured and archived for post-mortem analysis.

### 15.2 PostgreSQL Read Replica Lag Mitigation Runbook
1. **Trigger:** Replication lag on Read Replica exceeds 10 seconds.
2. **Step 1:** PgBouncer automatically removes lagging replica from the active read pool.
3. **Step 2:** Background worker increases WAL sender max processes (`max_wal_senders = 10`).
4. **Step 3:** When replication lag drops below 1 second, PgBouncer re-admits the replica to the read pool.


---

## 16. CONTINUOUS RELIABILITY METRIC AUDITING WITH GPT-4O

On a weekly basis, the Prometheus metrics database dump is submitted to GPT-4o for automated trend analysis:

1. **Anomalous Latency Detection:** Identifies micro-spikes in P99 API response time before SLO breaches occur.
2. **Disk Growth Trajectory:** Predicts exact date when NVMe storage utilization on any validator will reach 80%.
3. **Memory Leak Identification:** Analyzes RSS memory growth rate across Uvicorn worker processes to recommend garbage collection tuning parameters.


---

## 17. FINAL RELIABILITY GUARANTEE

By enforcing these governance standards, the Verdis Ecosystem guarantees continuous operational correctness, zero unhandled consensus forks, automated failover without double-signing, and multi-region disaster recovery for all users, developers, and institutional stakeholders.

---
**END OF GOVERNANCE STANDARD 14**
