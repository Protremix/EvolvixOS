# 19. SCALABILITY STRATEGY

## 19.1 BASELINE CURRENT CAPACITY (SINGLE SERVER SPECIFICATION)

AegisOS is an enterprise-grade AI Engineering Operating System designed to autonomously plan, execute, verify, and maintain complex software projects across web, mobile, smart contracts, microservices, and AI pipelines. At initial deployment (Phase 1 MVP), AegisOS operates on a single dedicated high-performance bare-metal or virtualized server instance.

### 19.1.1 Single Server Reference Hardware Specification
- **Compute:** 64 vCPUs (AMD EPYC 9554 or Intel Xeon Platinum 8480+ @ 3.1GHz+).
- **Memory:** 256 GB ECC DDR5 RAM (4800 MT/s).
- **Storage:** 2x 2.0 TB NVMe SSDs configured in RAID-1 (Enterprise Class, 7,000 MB/s read, 6,000 MB/s write, 1,000,000 Random IOPS).
- **Network Interface:** Dual 10 Gbps redundant NICs (Bonded, active-backup or 802.3ad LACP).
- **Operating System:** Ubuntu Server 24.04 LTS (Kernel 6.8+ tuned for containerization and high network throughput).

### 19.1.2 Hardware Resource Allocation Breakdown

On a single server, all AegisOS core components co-exist inside containerized environments managed by Docker Compose and gVisor runtime sandboxes. Resource budgets are allocated according to system priorities:

| Component | CPU Allocation | Memory Budget | Storage Bandwidth / I/O Budget | Role & Operational Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **API Gateway (Traefik v3)** | 4 vCPUs | 8 GB RAM | Minimal NVMe (Log buffers) | TLS termination, HTTP/WebSocket ingress, rate limiting |
| **Backend Core (FastAPI)** | 12 vCPUs | 32 GB RAM | 100 MB/s disk I/O | Control plane, REST/gRPC endpoints, FSM lifecycle |
| **Temporal Engine + Worker** | 8 vCPUs | 32 GB RAM | 200 MB/s disk I/O (Saga state) | Durable workflow execution, activity polling, retry state |
| **PostgreSQL 16 + pgvector** | 16 vCPUs | 64 GB RAM | 50,000 IOPS, 2,000 MB/s I/O | Relational metadata, vector embeddings, transactional log |
| **Redis 7 (Cache & Queue)** | 4 vCPUs | 32 GB RAM | Minimal NVMe (AOF append) | Ephemeral token streaming, distributed locking, pub/sub |
| **Agent Execution Sandboxes** | 16 vCPUs | 80 GB RAM | 50,000 IOPS (Scratch workspaces) | Isolated gVisor containers running builds, tests, LLM tools |
| **Host System & Monitoring** | 4 vCPUs | 8 GB RAM | 10,000 IOPS (Metrics/Logs) | OS overhead, Prometheus, Vector, FluentBit, Node Exporter |

### 19.1.3 Maximum Single-Server System Capacities

Under peak load, a fully optimized single server with the reference hardware achieves the following operational limits:

```
+-----------------------------------------------------------------------------------+
|                        SINGLE SERVER HARDWARE CAPACITY BOUNDS                     |
+-----------------------------------------------------------------------------------+
| Total Active Projects Managed:              1,000 Projects                        |
| Maximum Concurrent Executing Agents:         100 Active Agent Sandboxes           |
| Control Plane API Ingress Throughput:       10,000 Requests / Minute (166 req/s)   |
| Streaming Event Ingestion (Logs/Telemetry): 50,000 Events / Second                |
| Vector Search Query Throughput (pgvector):   250 Queries / Second (sub-50ms P99)   |
| Maximum Workspace File Indexing Rate:       500 Files / Second (AST + Embeddings) |
| Active WebSockets / SSE Connections:        2,000 Concurrent Streams              |
+-----------------------------------------------------------------------------------+
```

---

## 19.2 COMPREHENSIVE BOTTLENECK ANALYSIS

As load scales toward or beyond the single-server capacity thresholds, specific hardware and software components degrade at different rates. The following analysis details what breaks first, the physical limits triggering failure, and the compounding operational consequences.

```
                  SINGLE-SERVER BOTTLENECK CASCADING TIMELINE
                  
  Load Increase ---> [1. Agent Execution] ---> [2. Database Connections] 
                            |                         |
                            v                         v
                     (Memory Saturation)      (Connection Exhaustion)
                            |                         |
                            v                         v
                     [3. Redis Event Lag] ---> [4. API Gateway Drops]
```

### 19.2.1 Primary Bottleneck: Agent Execution & Sandbox Containment
- **Failure Trigger:** Exceeding 100 concurrent active agents or 80 GB RAM allocated to gVisor container runboxes.
- **Root Cause:** Each active execution sandbox spins up a gVisor (`runsc`) sandbox container to isolate execution (compilation, bash tool execution, code linting, unit tests). A single gVisor instance consumes ~250 MB static overhead plus dynamic process memory (Node.js, Python, Rust toolchains requiring 500 MB - 2 GB RAM per task).
- **Degradation Symptom:** Out-Of-Memory (OOM) killer terminations inside agent containers, swap thrashing on the host NVMe, high PTY wait latencies, and agent task timeout failures.
- **Physical Limit:** Memory exhaustion occurs prior to CPU exhaustion during full-stack compilation runs.

### 19.2.2 Secondary Bottleneck: Database Connection Exhaustion & Vector Search Overhead
- **Failure Trigger:** > 300 concurrent backend connections or > 250 vector similarity queries/sec.
- **Root Cause:** PostgreSQL 16 process-per-connection architecture incurs ~10 MB RAM allocation per connection. When 100 active agents continuously perform semantic context retrieval over HNSW vector indexes while control plane REST endpoints query project state, PostgreSQL process context switching degrades CPU cache efficiency.
- **Degradation Symptom:** PostgreSQL query latency spikes from 5ms to >2,000ms; `shared_buffers` contention; connection pool starvation in FastAPI backend services (`psycopg2` / `asyncpg` timeout exceptions).

### 19.2.3 Tertiary Bottleneck: Redis Memory & Event Stream Lag
- **Failure Trigger:** Streaming > 50,000 log events/sec from 100 active agent sandboxes.
- **Root Cause:** Redis 7 processes pub/sub and stream additions on a primary event loop thread. When agent log output (stdout/stderr streaming from builds and test suites) floods Redis streams (`stream:agent:logs:{task_id}`), single-threaded CPU core utilization hits 100%.
- **Degradation Symptom:** Pub/Sub message dropping, buffer memory expansion consuming Redis 32 GB RAM ceiling, delayed UI real-time streaming updates, and broken heartbeat signals in Temporal workflow execution.

### 19.2.4 Quaternary Bottleneck: API Gateway & Socket Connection Limits
- **Failure Trigger:** > 2,000 active concurrent WebSocket / Server-Sent Events (SSE) connections.
- **Root Cause:** Traefik v3 gateway holding open persistent HTTP/1.1 and HTTP/2 connections consumes file descriptors and kernel socket memory (`tcp_wmem`, `tcp_rmem`).
- **Degradation Symptom:** Socket buffer memory allocation failures, high TCP handshake latency, dropped HTTP connections for REST management endpoints, and standard HTTP 504 Gateway Timeouts.

---

## 19.3 VERTICAL SCALING PLAN

Before transitioning to multi-server distributed topologies, vertical hardware upgrades optimize cost-efficiency and minimize operational deployment complexity.

### 19.3.1 Hardware Upgrade Thresholds & Trigger Metrics

Vertical upgrades are triggered automatically when hardware metrics cross defined 15-minute sustained thresholds:

```
+-----------------------------------------------------------------------------------------+
|                              VERTICAL SCALING TRIGGER METRICS                           |
+------------------------+-------------------+--------------------+-----------------------+
| Hardware Resource      | Warning Threshold | Critical Trigger   | Action Required       |
+------------------------+-------------------+--------------------+-----------------------+
| CPU Utilization        | > 75% for 30 min  | > 85% for 15 min   | Upgrade vCPU Core Count|
| System Memory (RAM)    | > 80% allocated   | > 90% allocated    | Upgrade RAM Capacity  |
| NVMe Disk IOPS         | > 60,000 IOPS      | > 85,000 IOPS      | Upgrade NVMe Array    |
| NVMe Disk Capacity     | > 70% used        | > 85% used         | Expand NVMe Storage   |
| TCP Socket Queue       | > 1,000 queued    | > 5,000 queued     | Tune Kernel / Network |
+------------------------+-------------------+--------------------+-----------------------+
```

### 19.3.2 Server Upgrade Tiers

```
+-------------------------------------------------------------------------------------------------------+
|                                    VERTICAL HARDWARE TIER EVOLUTION                                   |
+--------------------+---------------------+--------------------+--------------------+------------------+
| Tier Level         | vCPU Count          | System RAM         | NVMe Storage Array | Target Concurrent|
|                    |                     |                    |                    | Agent Sandboxes  |
+--------------------+---------------------+--------------------+--------------------+------------------+
| **Tier 1 (Entry)** | 32 vCPU (3.0 GHz)   | 128 GB DDR5        | 1x 2TB NVMe        | 40 Active Agents |
| **Tier 2 (Mid)**   | 64 vCPU (3.1 GHz)   | 256 GB DDR5        | 2x 2TB NVMe RAID-1 | 100 Active Agents|
| **Tier 3 (Max)**   | 128 vCPU (3.4 GHz)  | 512 GB DDR5        | 4x 4TB NVMe RAID-10| 250 Active Agents|
+--------------------+---------------------+--------------------+--------------------+------------------+
```

### 19.3.3 Host OS Kernel & Runtime Tuning Parameters

When upgrading to Tier 3 vertical hardware, the underlying Linux kernel must be tuned via `/etc/sysctl.conf` to handle massive concurrency without socket starvation or disk I/O bottlenecks:

```ini
# /etc/sysctl.conf - AegisOS Single-Server High-Concurrency Tuning

# File Descriptor & Process Limits
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 8192

# Network Stack Tuning
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# Virtual Memory Tuning
vm.swappiness = 10
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.max_map_count = 1048576
```

---

## 19.4 HORIZONTAL SCALING EVOLUTION STRATEGY (5-PHASE ROADMAP)

When single-server vertical hardware limits (Tier 3) are reached, AegisOS transitions through 5 distinct horizontal architecture phases.

```
Phase 1: Single Server (MVP)
   [ All Services on 1 Host ]
               |
               v
Phase 2: Decoupled Infrastructure
   [ App Server ] <---> [ Dedicated DB ] <---> [ Dedicated Redis/NATS ]
               |
               v
Phase 3: Multi-App Stateless Core + Read Replicas
   [ Traefik LB ] ---> [ App Node 1 | App Node 2 ] <---> [ DB Primary + Read Replicas ]
               |
               v
Phase 4: Container Orchestration (Kubernetes / KEDA)
   [ K8s Ingress ] ---> [ Stateful Agent Worker Pools ] + [ DB Cluster + Sharding ]
               |
               v
Phase 5: Multi-Region Global Deployment
   [ Anycast DNS / CDN ] ---> [ US / EU / APAC Regional K8s Clusters ]
```

### 19.4.1 Phase 1: Single Server MVP Architecture
- **Target Scale:** 1 to 50 active projects, up to 30 concurrent agents.
- **Topology:** Single physical server running Docker Compose. All databases, application logic, and runner containers reside on a shared local bridge network (`aegis_net`).
- **Data Persistence:** Local NVMe host volume mounts (`/var/lib/postgresql/data`, `/var/lib/redis`, `/var/aegis/workspaces`).

### 19.4.2 Phase 2: Decoupled Infrastructure Architecture
- **Target Scale:** 50 to 300 active projects, up to 100 concurrent agents.
- **Topology:** Physical separation of application compute, database, and caching layers into dedicated server instances connected over a 10 Gbps private local area network (LAN).
- **Node Breakdown:**
  1. **App Server Node (64 vCPU, 128GB RAM):** Traefik v3, FastAPI Core, Temporal Workflow Service, gVisor agent runtime.
  2. **Database Node (32 vCPU, 128GB RAM, RAID-1 NVMe):** PostgreSQL 16 + pgvector, tuned shared memory.
  3. **Cache & Event Bus Node (16 vCPU, 64GB RAM):** Redis 7 (AOF enabled) + NATS JetStream server.

```
+-----------------------------------------------------------------------------------+
|                            PHASE 2 DECOUPLED TOPOLOGY                             |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +---------------------------+       10 Gbps Private Network                      |
|  |     APP SERVER NODE       |                                                    |
|  |  [Traefik v3 Gateway]     | <==============================================+   |
|  |  [FastAPI Backend Core]   |                                                |   |
|  |  [Temporal Workflow Engine|                                                |   |
|  |  [gVisor Agent Sandboxes] | <==========================+                   |   |
|  +---------------------------+                            |                   |   |
|                                                           v                   v   |
|                                              +------------------+   +-------------+
|                                              | DATABASE NODE    |   | CACHE NODE  |
|                                              | [PostgreSQL 16]  |   | [Redis 7]   |
|                                              | [pgvector]       |   | [NATS]      |
|                                              +------------------+   +-------------+
+-----------------------------------------------------------------------------------+
```

### 19.4.3 Phase 3: Multi-App Stateless Core + Load Balancer + Read Replicas
- **Target Scale:** 300 to 1,000 active projects, up to 300 concurrent agents.
- **Topology:** Stateless application layer scaled across 3+ compute instances behind an HA Load Balancer pair (Keepalived + HAProxy or Traefik HA cluster). PostgreSQL database scales via 1 Primary Write Node and 2 Streaming Read Replicas using PgBouncer connection poolers.
- **State Management:** WebSessions, agent state, and temporal execution state stored externally in Redis Cluster; local application servers retain zero state.

### 19.4.4 Phase 4: Container Orchestration (Kubernetes / KEDA Architecture)
- **Target Scale:** 1,000 to 10,000 active projects, 100 to 1,000 concurrent agents.
- **Topology:** Production Kubernetes (EKS, GKE, or Bare-Metal RKE2) cluster. Control plane runs in dedicated system node pools. Agent sandboxes are provisioned dynamically as Kubernetes Pods using custom gVisor (`runsc`) RuntimeClasses and isolated network policies.
- **Auto-Scaling:** Kubernetes Event-driven Autoscaling (KEDA) monitors NATS JetStream queue depth and CPU/Memory utilization to auto-scale agent worker pods from 10 to 1,000+ pods in seconds.

### 19.4.5 Phase 5: Multi-Region Global Enterprise Architecture
- **Target Scale:** 10,000+ active projects, 1,000+ concurrent agents, 100,000+ API requests/min globally.
- **Topology:** Global Anycast routing (Cloudflare Enterprise / AWS Route53 Latency-Based Routing) steering clients to three primary geographical regions (US-East, EU-Central, APAC-East).
- **Data Synchronization:** Primary write region with active-passive read-replica clusters in secondary regions; cross-region asynchronous vector index synchronization; localized agent execution pools storing transient build artifacts in regional S3 buckets.

---

## 19.5 DATABASE SCALING STRATEGY

PostgreSQL 16 serves as the primary relational and vector storage engine for AegisOS. As workload volume increases, database scaling progresses through connection pooling, read replication, declarative table partitioning, and horizontal sharding.

```
                          POSTGRESQL SCALING TOPOLOGY
                          
       [ Application Core / GraphQL / gRPC ]
                         |
                         v
                [ PgBouncer Pooler ]
                         |
         +---------------+---------------+
         | (Writes)                      | (Reads)
         v                               v
  +--------------+  Streaming Sync  +--------------+
  | PRIMARY NODE | ---------------> | READ REPLICA |
  +--------------+                  +--------------+
         |                                 |
         +--------------+------------------+
                        |
                        v
          [ Citus Sharded Partitions ]
```

### 19.5.1 Connection Pooling with PgBouncer
To prevent connection overhead, PgBouncer is deployed between application nodes and PostgreSQL:
- **Pooling Mode:** Transaction pooling (`pool_mode = transaction`).
- **Max Client Connections:** 10,000 client connections accepted at PgBouncer.
- **Default Pool Size:** 50 persistent server connections per PostgreSQL instance.
- **Reserve Pool Size:** 15 extra burst connections for peak transaction periods.

### 19.5.2 Read Replicas & CQRS Pattern
AegisOS separates Command (Write) and Query (Read) paths at the ORM / Database driver layer:
- **Primary Node:** Handles all INSERT, UPDATE, DELETE statements, workflow state updates, and transactional locks.
- **Read Replicas (2+ Nodes):** Handle read-only API requests, analytics, project dashboard fetches, and vector similarity searches (`pgvector`).
- **Replication Lag Management:** Replicas use PostgreSQL physical streaming replication with WAL sender processes. Maximum allowable replication lag is set to 500ms; if lag exceeds threshold, read queries automatically route to the primary.

### 19.5.3 Declarative Table Partitioning Strategy
High-volume append-only tables are partitioned declaratively by range (timestamp) and hash (`project_id`) to maintain small index sizes and fast vacuum times:

```sql
-- Partitioning High-Volume Agent Logs by Range (Monthly) and Hash (Project)
CREATE TABLE agent_execution_logs (
    log_id UUID NOT NULL,
    project_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    log_level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    PRIMARY KEY (created_at, project_id, log_id)
) PARTITION BY RANGE (created_at);

-- Monthly Partition Tables
CREATE TABLE agent_execution_logs_2026_08 PARTITION OF agent_execution_logs
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00')
    PARTITION BY HASH (project_id);

CREATE TABLE agent_execution_logs_2026_08_p1 PARTITION OF agent_execution_logs_2026_08
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE agent_execution_logs_2026_08_p2 PARTITION OF agent_execution_logs_2026_08
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

### 19.5.4 Horizontal Sharding Strategy
When total project data exceeds 5 TB or 10,000 active projects:
- **Sharding Engine:** Citus extension for distributed PostgreSQL.
- **Distribution Column:** `tenant_id` / `workspace_id`.
- **Query Routing:** Queries containing `workspace_id` route directly to the specific database shard node, eliminating cross-shard network joins.
- **Vector Index Optimization:** `pgvector` HNSW indexes are built locally on each shard node with `m = 16`, `ef_construction = 64`, keeping vector index structures entirely within node RAM.

---

## 19.6 AGENT SCALING ARCHITECTURE

Agents in AegisOS execute code, linting, unit tests, git commits, and LLM tool invocations. Agent scaling requires isolated execution, strict resource bounds, fast cold-start performance, and dynamic execution pools.

```
                      AGENT CONTAINER SPAWNING LIFECYCLE
                      
  [ Queue Task ] ---> [ Pre-Warmed gVisor Pool ] ---> [ Attach Workspace Volume ]
                                                             |
                                                             v
  [ Reclaim Sandbox ] <--- [ Cleanup Workspace ] <--- [ Execute Agent Task ]
```

### 19.6.1 Pre-Warmed Agent Sandbox Pools
To eliminate container cold-start latencies (1-3 seconds), AegisOS maintains a pool of pre-warmed gVisor sandboxes:
- **Pool Target Size:** 15% of active execution capacity (e.g., 15 warm sandboxes for a 100-agent tier).
- **Pre-allocation:** Container rootfs mounted with read-only base images (Node.js, Python, Rust, Go pre-installed).
- **Startup Time:** Reduced from 2,800ms to < 150ms via Linux container snapshot restoration and overlayfs mounts.

### 19.6.2 Dynamic Spawning & Isolation Engine
- **Runtime Security:** gVisor (`runsc`) sandbox runtime providing user-space kernel intercept.
- **Isolation Boundaries:**
  - Network namespace isolated (No direct outbound WAN access except via local proxy with strict domain allowlists for API calls).
  - Memory & CPU cgroups v2 boundaries strictly enforced.
  - Disk access constrained to ephemeral tmpfs or dedicated workspace overlay volumes.

### 19.6.3 Granular Agent Resource Quotas

Each agent tier is assigned explicit Linux cgroup v2 boundaries:

| Agent Profile Class | Target Tasks | vCPU Limit | vCPU Soft Cap | RAM Hard Limit | Ephemeral Storage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Micro Agent** | Code formatting, AST analysis, Git status | 0.5 vCPU | 0.2 vCPU | 512 MB | 2 GB tmpfs |
| **Standard Agent** | Feature development, unit testing, refactoring | 2.0 vCPU | 1.0 vCPU | 4,096 MB | 10 GB Overlay |
| **Heavy Agent** | Full build compilation, container build, integration tests | 8.0 vCPU | 4.0 vCPU | 16,384 MB | 50 GB NVMe Mount |

---

## 19.7 EVENT BUS & STREAMING SCALING

AegisOS relies on real-time event distribution for telemetry streaming, log propagation, agent workflow signals, and UI notification feeds.

```
                      EVENT BUS ARCHITECTURE & MIGRATION PATH
                      
  Phase 1 - 3 (Low to Mid Scale):
  [ Agents ] ---> [ Redis 7 Streams ] ---> [ FastAPI SSE / WebSocket ]
  
  Phase 4 - 5 (Enterprise Scale):
  [ Agents ] ---> [ NATS JetStream / Apache Kafka Cluster ] ---> [ Stream Workers ]
```

### 19.7.1 Phase 1-3: Redis Streams & NATS JetStream Configuration
- **Redis Streams:** Used for ultra-low latency (<5ms) ephemeral message pass-through. Ring buffers capped at `MAXLEN ~ 100000` per log stream to enforce strict RAM bounds.
- **NATS JetStream:** Used for guaranteed state transitions and workflow activity triggers. Configured with file-backed stream persistence and 3x replica distribution across nodes.

### 19.7.2 Phase 4-5: Apache Kafka Migration Strategy
When event throughput exceeds 100,000 events/sec, AegisOS migrates telemetry streams from Redis to an Apache Kafka / Strimzi Kubernetes cluster:
- **Topic Naming Standard:** `aegis.events.{tenant_id}.{project_id}.{event_type}`.
- **Partitioning Strategy:** Partitioned by `project_id` to guarantee strict chronological ordering of execution logs and state transitions within a given project.
- **Retention Policies:** Log stream topics set to 7-day retention with ZSTD compression enabled; state change topics set to infinite retention with log compaction enabled (`cleanup.policy = compact`).

---

## 19.8 CACHE SCALING STRATEGY

Cache performance is critical to prevent vector search and database lookup saturation during high concurrency.

```
                        TWO-TIER CACHING TOPOLOGY
                        
  [ Client / Agent Request ]
              |
              v
  +-----------------------+      Cache Hit (0.1ms)
  | L1 Memory Cache (LRU) | --------------------------+
  +-----------------------+                           |
              | Cache Miss                            |
              v                                       |
  +-----------------------+      Cache Hit (1.5ms)    |
  | L2 Redis Cluster      | --------------------------+
  +-----------------------+                           |
              | Cache Miss                            v
              v                             [ Return Response ]
  +-----------------------+                           ^
  | PostgreSQL Database   | --------------------------+
  +-----------------------+
```

### 19.8.1 Multi-Tier Caching Architecture
- **L1 Cache (In-Memory Application Cache):** Process-local LRU cache inside FastAPI workers (using Python `async-lru` / C++ bindings) with 1,000 entry capacity for fast context lookups (TTL: 5 seconds).
- **L2 Cache (Distributed Redis Cluster):** Multi-node Redis 7 cluster utilizing Redis Cluster sharding (16,384 hash slots across 3 primary nodes and 3 replica nodes).

### 19.8.2 Cache Invalidation & Stampede Mitigation
- **Cache Stampede Prevention:** Singleflight locking pattern implemented across FastAPI workers. When an L2 cache key expires, only a single backend worker queries PostgreSQL while other concurrent workers wait for the singleflight lock release.
- **Invalidation Strategy:** Event-driven invalidation via Redis Pub/Sub. Modifications to project metadata trigger instant key eviction (`DEL project:{id}:metadata`) across all connected L1/L2 caches.

---

## 19.9 API GATEWAY & BACKPRESSURE STRATEGY

To preserve core system stability when incoming traffic spikes reach 10,000+ API requests/min, the API gateway enforces token-bucket rate limiting and circuit-breaker backpressure.

```
                        API BACKPRESSURE & QUEUING PIPELINE
                        
  [ Incoming HTTP / WS Request ]
                |
                v
  [ Traefik Rate Limiter ] ---> (Exceeded Token Bucket) ---> [ HTTP 429 Too Many Requests ]
                |
                +---> (Within Limits) ---> [ FastAPI Concurrency Semaphore ]
                                                    |
                                                    +---> (Queue Full) ---> [ HTTP 503 Service Unavailable ]
                                                    |
                                                    +---> (Slot Available) ---> [ Execute Controller ]
```

### 19.9.1 Multi-Tier Rate Limiting Matrix
Rate limits are enforced by Traefik v3 using Redis-backed token buckets:

| Request Class | Rate Limit (Requests/Min) | Burst Allowance | Penalty / Action |
| :--- | :--- | :--- | :--- |
| **Anonymous / Public API** | 60 req/min | 10 requests | HTTP 429 + 60s cooldown |
| **Authenticated User UI** | 600 req/min | 50 requests | HTTP 429 + 10s cooldown |
| **Active Agent Sandbox** | 3,000 req/min | 200 requests | Queue backpressure throttle |
| **Enterprise Webhooks** | 1,200 req/min | 100 requests | HTTP 429 + Exponential Retry |

### 19.9.2 Circuit Breakers & Request Queuing
- **FastAPI Concurrency Semaphores:** Limits active in-flight REST handler processing to 500 concurrent connections.
- **Circuit Breaker States:**
  - **Closed (Normal):** Requests pass through normally.
  - **Open (Tripped):** When backend error rate (HTTP 5xx) exceeds 15% over 30 seconds, circuit opens immediately, returning cached or graceful failure responses for 15 seconds.
  - **Half-Open (Testing):** Trial requests are permitted to verify upstream service recovery.

---

## 19.10 FILE STORAGE & ARTIFACT SCALING

Code repositories, build binaries, diff patches, and agent snapshots require scalable object storage as file volume grows beyond single-server NVMe capacities.

```
                       STORAGE ARCHITECTURE MIGRATION
                       
  Phase 1 - 2: Local NVMe Storage (/var/aegis/artifacts)
  Phase 3 - 4: MinIO S3-Compatible On-Premises Cluster
  Phase 5: Cloud Native S3 / Cloudflare R2 + CDN Edge Caching
```

### 19.10.1 Object Storage Migration Path
- **Local NVMe Storage (Phase 1-2):** Workspace files stored directly under `/var/aegis/workspaces/{project_id}`.
- **Distributed Object Storage (Phase 3-5):** Full migration to S3 API-compatible storage (MinIO Enterprise or AWS S3 / Cloudflare R2).
- **Direct-to-S3 Uploads:** Agent binaries and heavy build logs bypass application servers entirely using S3 Presigned URLs generated by FastAPI control plane.

### 19.10.2 Lifecycle & Compression Rules
- **Active Workspace Artifacts:** Stored in S3 Standard / Hot storage tier.
- **Build Logs & Traces (> 30 days old):** Automatically migrated to S3 Infrequent Access (IA) with ZSTD compression.
- **Archived Project Snapshots (> 90 days old):** Automatically transitioned to Glacier / Cold storage; deleted permanently after user-configured retention limits.

---

## 19.11 COST OPTIMIZATION AT EACH SCALE PHASE

Scaling infrastructure while controlling operational expenditure requires aggressive resource optimization, spot instance utilization, and LLM query caching.

### 19.11.1 Infrastructure Cost Breakdown Schedule

| Scale Phase | Target Concurrent Capacity | Hardware / Cloud Configuration | Estimated Monthly Infrastructure Cost |
| :--- | :--- | :--- | :--- |
| **Phase 1 (MVP)** | 1,000 Projects / 100 Agents | 1x Dedicated Bare-Metal Server (64 vCPU, 256GB RAM) | $450 / month |
| **Phase 2 (Decoupled)**| 3,000 Projects / 250 Agents | 3x Dedicated Servers (App, DB, Redis) | $1,350 / month |
| **Phase 3 (Multi-App)**| 10,000 Projects / 600 Agents| 6x Cloud VMs + Managed Postgres + Load Balancers | $4,800 / month |
| **Phase 4 (K8s Cluster)**| 50,000 Projects / 2,500 Agents| Managed Kubernetes Cluster + Spot Worker Nodes | $18,500 / month |
| **Phase 5 (Multi-Region)**| 250,000+ Projects / 10,000+ Agents| Global Multi-Region K8s + Cross-Region S3 | $65,000 / month |

### 19.11.2 Cost Reduction Levers
1. **Spot / Preemptible Instance Pools:** Agent sandboxes run entirely on Spot Kubernetes worker nodes, reducing compute costs by up to 70%. Temporal workflow state safety guarantees task re-execution if a spot node is reclaimed.
2. **LLM Prompt & Response Semantic Caching:** Shared prompt/response vector caching via Redis eliminates redundant LLM API calls, reducing external API billings by 25-40%.
3. **Auto-Pausing Idle Workspaces:** Workspaces without active agent runs or developer WebSocket connections for > 15 minutes have their sandboxes hibernated and state compressed to object storage.

---

## 19.12 MONITORING THRESHOLDS FOR AUTO-SCALING

Auto-scaling policies in Kubernetes (HPA / KEDA) and host-level scripts trigger horizontal scale-out and scale-in events based on Prometheus metrics.

```
                      PROMETHEUS AUTO-SCALING PIPELINE
                      
  [ Prometheus Metrics ] ---> [ Alertmanager / KEDA Scaler ]
                                         |
                                         +---> [ High Metrics ] ---> [ Scale Out (+Pods/Nodes) ]
                                         |
                                         +---> [ Low Metrics ]  ---> [ Scale In (-Pods/Nodes) ]
```

### 19.12.1 Auto-Scaling Policy Matrix

| Metric Name | Prometheus Metric Query | Scale-Out Threshold | Scale-In Threshold | Scale Action |
| :--- | :--- | :--- | :--- | :--- |
| **API Gateway CPU** | `sum(rate(container_cpu_usage_seconds_total{app="traefik"}[2m]))` | > 70% CPU for 3 min | < 25% CPU for 10 min | Scale App Pods (+2 / -1) |
| **Queue Depth** | `nats_stream_messages_unacknowledged{stream="agent_tasks"}` | > 50 pending tasks | == 0 pending tasks | Scale Agent Workers (+5 / -2) |
| **Agent Memory Saturation**| `container_memory_working_set_bytes{container="agent"}` | > 85% allocated RAM | < 30% allocated RAM | Provision Node (+1 Node) |
| **DB Connection Pool** | `pgbouncer_pools_server_active / pgbouncer_pools_server_max` | > 80% saturation | < 30% saturation | Scale Read Replicas (+1 Replica) |
| **HTTP P99 Latency** | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | > 800 ms | < 150 ms | Scale FastAPI Core (+3 Pods) |

---


# 20. DISASTER RECOVERY STRATEGY

## 20.1 COMPREHENSIVE RISK ASSESSMENT & THREAT MODELING

AegisOS must maintain enterprise resilience against system failures, operational accidents, cloud infrastructure disruptions, data corruption, and malicious attacks. The following matrix categorizes all potential failure vectors, their blast radius, and preventive mitigations.

| Failure Vector | Cause / Scenario | Impact & Blast Radius | Likelihood | Mitigation Architecture |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Host Failure** | Motherboard, CPU, or Kernel panic on single server | Total system outage for all projects & agents | Medium | Automated health check failover, cold standby host |
| **Disk / Storage Loss** | NVMe drive failure, RAID controller failure, corruption | Data loss of un-synced database & files | Low | RAID-1/RAID-10 arrays, continuous WAL sync to offsite S3 |
| **Database Corruption** | Power loss during write, file system crash, storage bug | PostgreSQL table or vector index unreadable | Very Low | Daily pg_dump, continuous WAL archiving for Point-In-Time Recovery |
| **Redis Memory Crash** | OOM killer termination, unhandled Redis process crash | Loss of transient logs, queue state, UI sessions | Medium | Dual RDB + AOF persistence, Redis Sentinel / Cluster auto-failover |
| **Network Partition** | Cloud provider switch fail, ISP fiber cut, DDoS attack | Inability for users/agents to access control plane | Medium | Multi-region DNS failover, Cloudflare DDoS protection |
| **Human Operator Error** | Accidental `DROP TABLE`, `rm -rf`, bad migration script | Customer project or database state destruction | Medium | Role-Based Access Control (RBAC), immutable backup snapshots |
| **Ransomware / Malware** | Compromised agent sandbox escape or API key leakage | Encrypted volumes or compromised system security | Low | gVisor runtime sandbox isolation, read-only rootfs, immutable backups |

---

## 20.2 SERVICE LEVEL OBJECTIVES & RECOVERY OBJECTIVES (RTO / RPO)

Recovery Time Objective (RTO) defines the maximum acceptable duration of system downtime. Recovery Point Objective (RPO) defines the maximum acceptable data loss measured in time.

```
+-----------------------------------------------------------------------------------+
|                        RTO & RPO TARGET DEFINITIONS BY PHASE                      |
+-----------------------------------------------------------------------------------+
| MVP PHASE (Single Server / Decoupled):                                            |
|   - Recovery Time Objective (RTO):  <= 4 Hours                                    |
|   - Recovery Point Objective (RPO): <= 15 Minutes (PostgreSQL DB)                 |
|                                    <= 1 Hour (Workspace File Storage)             |
|                                    <= Ephemeral (Cache / Redis Queue)             |
+-----------------------------------------------------------------------------------+
| SCALE / ENTERPRISE PHASE (Kubernetes / Multi-Region):                             |
|   - Recovery Time Objective (RTO):  <= 1 Hour (Full Region Recovery)             |
|   - Recovery Point Objective (RPO): <= 5 Minutes (Database Transaction Log)       |
|                                    <= 5 Minutes (Object Storage Replicas)         |
|                                    <= 0 Seconds (Committed Git Code Base)         |
+-----------------------------------------------------------------------------------+
```

### 20.2.1 Detailed Service Component RTO/RPO Breakdown

| System Component | MVP RTO Target | MVP RPO Target | Scale RTO Target | Scale RPO Target | Primary Disaster Recovery Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL Database** | 2 Hours | 15 Minutes | 15 Minutes | 5 Minutes | Streaming Replication + WAL-G PITR |
| **Redis Cache / State** | 30 Minutes | Ephemeral | 5 Minutes | Ephemeral | RDB + AOF Snapshots / Sentinel Failover |
| **Workspace Repositories**| 4 Hours | 1 Hour | 15 Minutes | 5 Minutes | Offsite S3 Rsync / Cross-Region Replication |
| **API Gateway / Control** | 1 Hour | 0 Minutes | 5 Minutes | 0 Minutes | Stateless Container Re-deployment |
| **Agent Executions** | 4 Hours | Re-run Task | 1 hour | Re-run Task | Temporal Workflow Re-hydration |

---

## 20.3 MULTI-TIERED BACKUP ARCHITECTURE

To guarantee recovery against any failure scenario, AegisOS implements multi-tiered, automated backups across all data layers.

```
                          MULTI-TIER BACKUP PIPELINE
                          
   [ PostgreSQL Primary ] ---> Daily pg_dump --------> [ Local Backup Store ]
           |                                                    |
           +-----------------> WAL Archiving (WAL-G)            v
                                    |                 [ Encrypted Offsite S3 ]
                                    v                           ^
   [ Workspace Repositories ] -> Daily Rsync / Snapshot --------+
                                                                |
   [ System Configurations ] -> GitOps / Vault Engine ----------+
```

### 20.3.1 Database Backup Architecture (PostgreSQL 16)
- **Full Logical Snapshots:** Executed daily at 02:00 UTC using `pg_dumpall` with ZSTD compression (`level 9`). Retained locally for 7 days and pushed to offsite encrypted object storage.
- **Continuous Write-Ahead Logging (WAL) Archiving:** Managed via `WAL-G` or `pgBackRest`. Every completed WAL segment (16 MB) is instantly compressed and uploaded to offsite S3 storage.
- **Point-In-Time Recovery (PITR):** Enables exact database state restoration to any second within the past 30 days by combining the latest full daily backup with sequential WAL replay.

### 20.3.2 Redis Cache & Queue Preservation Strategy
- **Snapshot Persistence (RDB):** RDB snapshots triggered every 15 minutes if at least 100 key changes occur (`save 900 1`, `save 300 10`, `save 60 10000`).
- **Append-Only File (AOF):** Enabled with `appendfsync everysec`. Provides 1-second maximum state loss for queue state and agent heartbeat signals.
- **Offsite Export:** Daily export of consolidated RDB files to offsite S3 backup buckets.

### 20.3.3 File Storage & Code Repository Backups
- **Incremental Volume Sync:** Scheduled `rsync` with hardlinks or ZFS/Btrfs snapshotting executed every 6 hours from `/var/aegis/workspaces` to a dedicated secondary backup host.
- **S3 Bucket Lifecycle & Versioning:** S3 buckets configured with Object Versioning and S3 Cross-Region Replication (CRR) to replicate all project code diffs and build artifacts to a secondary geographical cloud region within 5 minutes.

### 20.3.4 Configuration & Infrastructure as Code (IaC)
- **Git Version Control:** 100% of deployment manifests (Docker Compose, Terraform, Helm charts, Kubernetes YAMLs, Ansible playbooks) are version-controlled in an offsite Git repository.
- **Secret Encryption:** All application secrets, SSL certificates, and database passwords are encrypted at rest using HashiCorp Vault or SOPS (Secrets OPerationS) with AWS KMS / GCP KMS encryption keys.

---

## 20.4 AUTOMATED BACKUP VERIFICATION & TESTING FRAMEWORK

A backup that has not been verified for restore integrity is considered invalid. AegisOS runs automated backup verification pipelines daily in an isolated test environment.

```
                     AUTOMATED BACKUP TEST PIPELINE
                     
  [ Schedule Trigger (03:00 UTC) ]
                 |
                 v
  [ Spin Up Isolated Docker Test Harness ]
                 |
                 v
  [ Download Latest pg_dump / WAL File from S3 ]
                 |
                 v
  [ Restore Database & Execute Integrity Battery ]
                 |
                 +---> (Success) ---> [ Teardown & Log Verification PASS ]
                 |
                 +---> (Failure) ---> [ Trigger PagerDuty Alert (SEV-1) ]
```

### 20.4.1 Automated Restore Test Pipeline Script

The following automated validation script runs daily inside an isolated continuous integration harness:

```bash
#!/usr/bin/env bash
set -euo pipefail

# AegisOS Daily Automated Backup Verification Harness
TEST_CONTAINER="aegis_db_verify_test"
TEST_PORT="55432"
LATEST_BACKUP_S3="s3://aegis-backups-offsite/postgres/daily_latest.sql.zst"
RESTORE_LOG="/var/log/aegis/backup_verify.log"

echo "[$(date -u)] Starting automated backup restoration test..." >> "${RESTORE_LOG}"

# 1. Pull down latest compressed backup
aws s3 cp "${LATEST_BACKUP_S3}" /tmp/verify_backup.sql.zst

# 2. Decompress backup file
zstd -d /tmp/verify_backup.sql.zst -o /tmp/verify_backup.sql --force

# 3. Spin up ephemeral PostgreSQL instance
docker run --name "${TEST_CONTAINER}" -e POSTGRES_PASSWORD=verify_secret -p "${TEST_PORT}:5432" -d postgres:16-alpine

# Wait for DB readiness
until docker exec "${TEST_CONTAINER}" pg_isready -U postgres; do
  sleep 2
done

# 4. Restore database schema and data
docker exec -i "${TEST_CONTAINER}" psql -U postgres < /tmp/verify_backup.sql >> "${RESTORE_LOG}" 2>&1

# 5. Execute synthetic integrity query battery
VERIFY_COUNT=$(docker exec -i "${TEST_CONTAINER}" psql -U postgres -d aegisos -t -c "SELECT COUNT(*) FROM projects;")

if [ "${VERIFY_COUNT}" -gt 0 ]; then
  echo "[$(date -u)] SUCCESS: Restored database contains ${VERIFY_COUNT} projects." >> "${RESTORE_LOG}"
  # Teardown
  docker stop "${TEST_CONTAINER}" && docker rm "${TEST_CONTAINER}"
  rm -f /tmp/verify_backup.sql*
  exit 0
else
  echo "[$(date -u)] CRITICAL FAILURE: Restored database integrity check failed!" >> "${RESTORE_LOG}"
  # Dispatch PagerDuty Alert
  curl -X POST https://events.pagerduty.com/v2/enqueue     -H 'Content-Type: application/json'     -d '{"routing_key": "SEV1_KEY", "event_action": "trigger", "payload": {"summary": "Backup Restoration Failed!", "severity": "critical", "source": "backup-verify-harness"}}'
  docker stop "${TEST_CONTAINER}" && docker rm "${TEST_CONTAINER}"
  exit 1
fi
```

---

## 20.5 AUTOMATED & MANUAL FAILOVER PROCEDURES

When catastrophic failures strike primary hardware or cloud availability zones, AegisOS triggers failover routines to restore operational status.

```
                          DATABASE FAILOVER WORKFLOW
                          
  [ Primary DB Failure Detected ] ---> [ Patroni / Sentinel Quorum Validation ]
                                                     |
                                                     v
  [ Promote Read Replica to Primary ] <--- [ Verify WAL Alignment ]
                 |
                 v
  [ Update PgBouncer / DNS Endpoint to Point to New Primary ]
```

### 20.5.1 Database Failover Procedure (PostgreSQL + Patroni)
1. **Failure Detection:** Patroni cluster manager issues heartbeat requests every 2 seconds to the primary PostgreSQL node. If the primary fails to respond for 10 seconds (5 failed probes), leader lease expires.
2. **Leader Election:** Active Patroni nodes consult Distributed Consensus Store (DCS - Etcd/Consul) to elect the read replica with the most advanced WAL LSN (Log Sequence Number).
3. **Replica Promotion:** The elected replica executes `pg_ctl promote` and exits recovery mode, transitioning to read-write Primary state.
4. **Traffic Rerouting:** PgBouncer connection poolers update target endpoints automatically via Consul-template or dynamic DNS update, routing application traffic to the new primary within < 15 seconds.

### 20.5.2 Application Control Plane Failover (DNS Switch)
If the entire primary data center or cloud host goes offline:
1. **Health Check Probe Failure:** External monitoring (UptimeRobot / Cloudflare Health Checks) detects HTTP 502/504 or ping loss on primary IP (`192.0.2.10`).
2. **Automated DNS Switch:** Cloudflare API / AWS Route53 Failover Routing Policy updates DNS `A` records for `api.aegisos.dev` to point to Standby Secondary Host (`198.51.100.20`).
3. **Standby Boot Activation:** Standby node executes automated recovery playbook (`ansible-playbook -i production recovery.yml`) to attach latest restored S3 storage volumes and launch containers.

### 20.5.3 Cache Failover Procedure (Redis Sentinel)
- **Sentinel Monitoring:** 3 Redis Sentinel instances monitor primary Redis node (`redis-primary`).
- **Quorum Agreement:** When 2 of 3 Sentinels declare `redis-primary` Subjectively Down (S-DOWN), state escalates to Objectively Down (O-DOWN).
- **Replica Promotion:** Sentinel selects the slave with highest priority and lowest replication offset, promoting it to master.
- **Client Reconfiguration:** FastAPI backend connects via Redis Sentinel client bindings, automatically receiving updated master IP without requiring application restart.

---

## 20.6 DATA CORRUPTION & STATE RECOVERY PROTOCOLS

Logical data corruption (e.g., accidental bulk deletion, corrupted vector indexes, or buggy database migrations) requires targeted surgical recovery rather than full server failover.

```
                      POINT-IN-TIME RECOVERY (PITR) FLOW
                      
  [ Corruption Event Occurs (14:32:10 UTC) ]
                     |
                     v
  [ Isolate System & Terminate Application Ingress ]
                     |
                     v
  [ Identify Exact Corruption Timestamp (14:32:09 UTC) ]
                     |
                     v
  [ Restore Last Full Base Backup + Apply WAL Segment Replay ]
                     |
                     v
  [ Stop WAL Replay at Target Time (14:32:09 UTC) ]
                     |
                     v
  [ Verify Table State & Re-Open Ingress ]
```

### 20.6.1 Step-by-Step Point-In-Time Recovery Execution Playbook
1. **Isolate Database:** Stop FastAPI application containers to halt all incoming write operations:
   ```bash
   docker compose -f docker-compose.prod.yml stop backend workers
   ```
2. **Identify Target Timestamp:** Inspect application logs or audit trails to identify the precise timestamp immediately preceding corruption (e.g., `2026-08-05 14:32:09.102451+00`).
3. **Prepare Target Recovery Instance:** Provision a fresh PostgreSQL container or directory mount.
4. **Configure `recovery.signal` and `postgresql.conf`:**
   ```ini
   # postgresql.conf recovery settings
   restore_command = 'wal-g wal-fetch "%f" "%p"'
   recovery_target_time = '2026-08-05 14:32:09+00'
   recovery_target_action = 'promote'
   ```
5. **Start Recovery:** Launch PostgreSQL. The database reads WAL files sequentially up to the specified `recovery_target_time`, pauses, and promotes itself to read-write status.
6. **Integrity Validation:** Execute SQL validation queries to confirm data cleanliness before updating PgBouncer routing.

---

## 20.7 ROLLBACK PROCEDURES (CODE, DATABASE, CONFIGURATION)

Failed software deployments must be reverted cleanly without causing state inconsistency between application code and database schema.

```
                         ZERO-DOWNTIME ROLLBACK ENGINE
                         
  [ Deployment Issue Detected ]
                |
                +---> Code Failure: Trigger Blue-Green Container Switchback
                |
                +---> Migration Failure: Run Forward-Compatible Down Migration
                |
                +---> Config Failure: Git Revert Commit + Apply Vault Snapshot
```

### 20.7.1 Code Rollback Protocol (Blue-Green / Rolling Rollback)
- **Container Strategy:** AegisOS uses tagged Docker images (`aegis-core:v1.4.2`, `aegis-core:v1.4.3`).
- **Rollback Command:**
  ```bash
  # Instant Rollback to Previous Image Tag
  docker compose -f docker-compose.prod.yml up -d --no-deps backend_v1_4_2
  ```
- **Kubernetes Rollback:**
  ```bash
  kubectl rollout undo deployment/aegis-backend-core -n aegisos
  ```

### 20.7.2 Database Migration Rollback Strategy
To prevent schema rollbacks from breaking active applications, all database migrations follow strict **Expand-Contract (Parallel Change)** design rules:
1. **Phase 1 (Expand):** Add new columns/tables as nullable or with defaults. Code supports both old and new schemas.
2. **Phase 2 (Migrate):** Backfill historical data in background transactions.
3. **Phase 3 (Contract):** Remove old columns/tables only after new code version is fully deployed and verified.

If a migration must be reverted immediately:
```bash
# Alembic / Goose Rollback Execution
alembic downgrade -1
```

### 20.7.3 Configuration Rollback Protocol
- Configuration state is driven by GitOps (ArgoCD / Flux / Git triggers).
- To revert invalid system configurations:
  ```bash
  git revert HEAD -m "Reverting invalid Traefik rate limit configuration"
  git push origin main
  # Automated CI/CD applies reverted state in < 120 seconds
  ```

---

## 20.8 DISASTER RECOVERY RUNBOOK (STEP-BY-STEP SCENARIOS)

This section provides explicit operational runbooks for key disaster scenarios.

### 20.8.1 Scenario A: Complete Primary Server Hardware Loss (Single Server MVP)

**Initial Symptom:** PagerDuty alert "Host Down - Ping and SSH Unreachable".
**Goal:** Spin up replacement server and restore complete operational capability within RTO (4 Hours).

```
   Step 1: Provision Replacement Host
   Step 2: Pull Infrastructure as Code Repository
   Step 3: Restore Database via WAL-G / pg_dump
   Step 4: Restore Workspace Files from S3 Backup
   Step 5: Launch AegisOS Core Services
   Step 6: Update Public DNS Endpoints
```

**Detailed Step-by-Step Execution Command Sequence:**

```bash
# 1. Provision new Bare-Metal / VM Instance (Ubuntu 24.04 LTS, 64 vCPU, 256GB RAM)
# 2. SSH into new instance and clone IaC repository
git clone https://github.com/aegisos/aegis-infrastructure.git /opt/aegisos
cd /opt/aegisos/deploy/single-server

# 3. Restore Environment Configuration & Vault Keys
aws s3 cp s3://aegis-backups-vault/env.production .env

# 4. Initialize Local Directory Structures
mkdir -p /var/lib/postgresql/data /var/lib/redis /var/aegis/workspaces

# 5. Download and Restore Latest Complete Database Backup
aws s3 cp s3://aegis-backups-offsite/postgres/latest_full.sql.zst /tmp/
zstd -d /tmp/latest_full.sql.zst -o /tmp/latest_full.sql

# Start Database Service Only
docker compose -f docker-compose.prod.yml up -d postgres
sleep 10
docker exec -i aegis_postgres psql -U postgres < /tmp/latest_full.sql

# 6. Restore Workspace Repository Artifacts from S3
aws s3 sync s3://aegis-workspaces-backup/latest /var/aegis/workspaces/

# 7. Start All Remaining AegisOS Services
docker compose -f docker-compose.prod.yml up -d

# 8. Update Public DNS Record via Cloudflare API
curl -X PUT "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID"      -H "Authorization: Bearer CF_API_TOKEN"      -H "Content-Type: application/json"      -d '{"type":"A","name":"api.aegisos.dev","content":"NEW_SERVER_IP","ttl":120,"proxied":true}'

# 9. Verify System Health Endpoint
curl -f https://api.aegisos.dev/healthz
```

---

### 20.8.2 Scenario B: Unrecoverable PostgreSQL Volume Corruption

**Initial Symptom:** PostgreSQL container crash looping with log `PANIC: could not locate a valid checkpoint record`.
**Goal:** Perform PITR restore to last healthy WAL checkpoint.

```bash
# 1. Stop all dependent backend services to prevent secondary corruption
docker compose -f docker-compose.prod.yml stop backend workers temporal

# 2. Rename corrupted data directory for post-mortem forensics
mv /var/lib/postgresql/data /var/lib/postgresql/data_corrupted_$(date +%Y%m%m_%H%M%S)
mkdir -p /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

# 3. Fetch Base Snapshot via WAL-G
wal-g backup-fetch /var/lib/postgresql/data LATEST

# 4. Create recovery.signal file
touch /var/lib/postgresql/data/recovery.signal

# 5. Append recovery parameters to postgresql.conf
cat << 'EOF' >> /var/lib/postgresql/data/postgresql.conf
restore_command = 'wal-g wal-fetch "%f" "%p"'
recovery_target_timeline = 'latest'
EOF

# 6. Launch PostgreSQL container to complete WAL replay
docker compose -f docker-compose.prod.yml up -d postgres

# Monitor recovery progress
docker logs -f aegis_postgres

# 7. Restart remaining services once database accepts connections
docker compose -f docker-compose.prod.yml up -d
```

---

## 20.9 INCIDENT COMMUNICATION & ESCALATION PROTOCOL

Clear escalation hierarchies prevent panic and ensure structured response during major system outages.

```
                      INCIDENT ESCALATION TRIAGE
                      
   [ Incident Detected ] ---> Severity Triage
                                 |
     +---------------------------+---------------------------+
     | SEV-0 / SEV-1                                         | SEV-2 / SEV-3
     v                                                       v
  [ Assemble Incident Command ]                            [ On-Call Engineer Fix ]
  - Incident Commander (IC)                                - Standard JIRA Ticket
  - Tech Lead Engine                                       - Next Business Day Fix
  - Communications Lead
     |
     v
  [ Publish Statuspage Notice & Notify Executives ]
```

### 20.9.1 Severity Categorization Matrix

| Severity Level | Threshold / Impact | Response Time SLA | Escalation Target |
| :--- | :--- | :--- | :--- |
| **SEV-0 (Critical)** | Total platform down, data loss risk, global outage | Immediate (< 5 mins) | CTO, VP Eng, All On-Call Engineers |
| **SEV-1 (High)** | Core agent execution impaired, API degraded >25% | < 15 minutes | Lead Architect, On-Call DevOps |
| **SEV-2 (Medium)**| Non-critical feature broken (e.g., export analytics) | < 2 hours | Component Team Lead |
| **SEV-3 (Low)** | Minor bug, cosmetic UI issue, low-impact glitch | < 24 hours | Standard Backlog Triage |

### 20.9.2 Incident Communication Templates

#### Template 1: Initial Customer Incident Notification (Statuspage)
> **Headline:** Investigating Degradation with Agent Execution Engine  
> **Status:** Investigating  
> **Impact:** Core Control Plane & Agent Sandboxes  
> **Message:** We are currently investigating an issue impacting agent task execution and real-time streaming updates. Our engineering team has identified the cause and is executing recovery procedures. Existing project repository data remains completely secure and unaffected. Next update will be provided in 30 minutes.

#### Template 2: Incident Resolution Notification
> **Headline:** Service Restored: Agent Execution Engine Operational  
> **Status:** Resolved  
> **Impact:** Core Control Plane & Agent Sandboxes  
> **Message:** Recovery procedures have been completed successfully, and all AegisOS services are fully operational. All queued agent execution tasks have resumed. A full Post-Incident Review (PIR) will be published within 48 hours.

---

## 20.10 POST-INCIDENT REVIEW (PIR) PROCESS

Within 48 hours of resolving any SEV-0 or SEV-1 incident, AegisOS conducts a blameless Post-Incident Review to identify system vulnerabilities and prevent recurrence.

```
                        BLAMELESS PIR TIMELINE
                        
  [ Incident Resolution ] ---> [ Compile Telemetry Logs ] (T+12h)
                                         |
                                         v
  [ Conduct PIR Meeting ] ---> [ Blameless 5-Whys Analysis ] (T+24h)
                                         |
                                         v
  [ Publish PIR Report & Assign Preventive Action Items ] (T+48h)
```

### 20.10.1 Post-Incident Review Template Structure
1. **Executive Summary:** High-level narrative of the outage, duration, customer impact, and resolution.
2. **Timeline of Events (UTC):** Minute-by-minute breakdown from trigger to detection, triage, mitigation, and resolution.
3. **Root Cause Analysis (5 Whys Framework):** Iterative questioning to unearth systemic architectural or procedural weaknesses.
4. **Impact Metrics:** Downtime duration, failed agent runs, HTTP error percentages, estimated financial impact.
5. **Corrective Action Items:** Explicit engineering tickets assigned to specific owners with strict 14-day completion SLAs.

---

## 20.11 BUSINESS CONTINUITY PLAN (BCP)

The Business Continuity Plan guarantees that AegisOS enterprise operations can endure vendor outages, office access disruptions, and key personnel absences.

### 20.11.1 Vendor & Cloud Provider Diversity Strategy
- **Multi-Cloud Vendor Fallback:** Primary compute resides on AWS / Dedicated Bare-Metal; secondary disaster target configured on Google Cloud Platform (GCP) or Hetzner Cloud.
- **LLM API Redundancy:** Application layer supports dynamic model routing. If primary LLM provider (Anthropic) experiences API outages, AegisOS automatically reroutes agent requests to secondary providers (OpenAI / Azure OpenAI) via unified provider interface.

### 20.11.2 Key Personnel Resilience ("Bus Factor" Mitigation)
- **On-Call Rotation:** Minimum of 4 senior engineers trained on DR runbooks.
- **Access Delegation:** Emergency break-glass admin credentials stored in dual-control Vault accounts requiring approval from 2 of 5 designated security custodians.
- **Runbook Automation:** All DR procedures documented as executable bash/ansible scripts to minimize reliance on institutional tribal knowledge during high-stress outages.

---

## 20.12 INSURANCE, LEGAL & LIABILITY CONSIDERATIONS

Operational resilience includes regulatory compliance, financial risk caps, and legal protections.

### 20.12.1 SLA Commitments & Service Credit Calculation

AegisOS Enterprise SLAs guarantee 99.9% uptime per calendar month. Outages exceeding allowable downtime trigger Service Credits calculated as a percentage of monthly subscription fees:

| Monthly Uptime Percentage | Service Credit Percentage Applied |
| :--- | :--- |
| **99.0% - 99.89%** | 10% Credit |
| **95.0% - 98.99%** | 25% Credit |
| **< 95.0%** | 50% Credit (Maximum Liability Cap) |

### 20.12.2 Cyber Liability Insurance Requirements
- **Coverage Limits:** $5,000,000 Cyber Liability & Data Breach Policy covering forensic investigation, customer notification costs, and legal defence.
- **Policy Compliance Mandates:** Annual third-party penetration testing, mandatory multi-factor authentication (MFA) across all administrative access endpoints, and verified immutable offsite backups.

### 20.12.3 Regulatory Compliance & Data Privacy Obligations
- **GDPR / CCPA Mandates:** Automated deletion pipelines enforcing complete tenant data destruction upon contract termination within 30 days, including offsite backup purge schedules.
- **SOC 2 Type II Audits:** Continuous logging of all administrative access, disaster recovery test results, and system modification audits maintained for 365 days.

---
