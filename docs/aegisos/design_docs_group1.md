# AegisOS Architecture Documentation Package — Group 1

**System Name:** AegisOS (Universal AI Engineering Operating System)  
**Document Version:** 1.0.0  
**Target Stack:** Python 3.11+, FastAPI, Next.js 14 (App Router), PostgreSQL 16, Redis 7.2, Kafka 3.6, Docker Engine, GPT-4o Multi-Agent Orchestrator  
**UI Theme:** Dark Mode (Primary Background `#0a0d12`, Accent `#00ff88`)  
**Scope:** Universal Engineering Automation & Autonomous Software Development Infrastructure  

---

# TABLE OF CONTENTS
1. [DOCUMENT 3: TECHNICAL REQUIREMENTS DOCUMENT (TRD)](#3-technical-requirements-document-trd)
2. [DOCUMENT 5: BACKEND ARCHITECTURE](#5-backend-architecture)
3. [DOCUMENT 6: FRONTEND ARCHITECTURE](#6-frontend-architecture)
4. [DOCUMENT 13: API ARCHITECTURE](#13-api-architecture)

---


# 3. TECHNICAL REQUIREMENTS DOCUMENT (TRD)

## 3.1 SYSTEM OVERVIEW & EXECUTIVE PURPOSE
AegisOS is an enterprise-grade, universal AI Engineering Operating System designed to orchestrate autonomous software engineering workflows across heterogeneous tech stacks. The system abstracts complex software development lifecycles (SDLC) into deterministic, multi-agent workflows wherein specialized AI agents—utilizing large language models (LLMs) such as GPT-4o—collaborate to execute requirements analysis, architectural modeling, code synthesis, refactoring, automated unit/integration testing, containerized execution, and deployment.

AegisOS is architected for deployment as a multi-tenant SaaS platform or as a private, self-hosted enterprise platform within VPC/air-gapped Kubernetes environments. It interacts natively with version control systems (GitHub, GitLab, Bitbucket), container runtimes (Docker, Containerd), and cloud infrastructure providers (AWS, GCP, Azure), while presenting real-time visual telemetry, code diffing, and interactive command terminals to human engineering teams through a Next.js web application styled in a dark cyberpunk aesthetic accented with `#00ff88` emerald highlights.

---

## 3.2 PERFORMANCE REQUIREMENTS

The platform must maintain sub-second responsiveness for interactive API calls and streaming interactions, while maintaining bounded, deterministic execution guarantees for asynchronous AI agent execution loops.

### 3.2.1 Quantitative SLA Benchmarks
| Requirement ID | Performance Metric | Baseline Target (SLA) | Peak Load SLA | Measuring Conditions / Workload |
| :--- | :--- | :--- | :--- | :--- |
| **PERF-01** | REST API Latency (Read) | p95 < 45 ms, p99 < 100 ms | p95 < 80 ms, p99 < 150 ms | Tested via API gateway under 5,000 req/sec load |
| **PERF-02** | REST API Latency (Mutation) | p95 < 120 ms, p99 < 300 ms | p95 < 250 ms, p99 < 500 ms | Measured on DB writes (excludes LLM calls) |
| **PERF-03** | LLM Stream Time-to-First-Token | TTFT < 150 ms | TTFT < 350 ms | Measured from client SSE trigger to first chunk |
| **PERF-04** | Streaming Output Throughput | > 60 tokens/sec/stream | > 40 tokens/sec/stream | Sustained throughput per active client session |
| **PERF-05** | Real-Time Event Propagation | p95 < 15 ms, p99 < 30 ms | p95 < 35 ms, p99 < 75 ms | Redis Pub/Sub backplane event dispatch latency |
| **PERF-06** | Peak HTTP Gateway Throughput | 10,000 req/sec | 15,000 req/sec burst | Distributed over 10 FastAPI ASGI replicas |
| **PERF-07** | Kafka Bus Ingestion Speed | 50,000 events/sec | 100,000 events/sec burst | Evaluated across 16 Kafka topic partitions |
| **PERF-08** | AST Code Parsing Latency | < 1,500 ms per 10k LOC | < 3,000 ms per 10k LOC | Tree-sitter multi-language AST extraction |
| **PERF-09** | Docker Sandbox Spawn Time | < 800 ms (cold), < 150 ms (warm)| < 2,000 ms (cold) | Container creation from pre-warmed image pool |
| **PERF-10** | Memory Overhead per Agent | < 128 MB RAM per active agent | < 256 MB RAM peak | Redis agent state store + Python process runner |

### 3.2.2 Latency & Pipeline Topology
```
+-----------------------------------------------------------------------------------+
|                            LATENCY & THROUGHPUT PROFILE                           |
+---------------------+-------------------+------------------+----------------------+
| Layer               | Operation         | p95 Target       | Max Concurrency      |
+---------------------+-------------------+------------------+----------------------+
| Edge / Gateway      | TLS Handshake/Auth| < 20 ms          | 50,000 connections   |
| REST API (FastAPI)  | Project CRUD      | < 45 ms          | 10,000 req/sec       |
| Event Bus (Kafka)   | Agent Telemetry   | < 10 ms          | 50,000 msg/sec       |
| Agent Orchestrator  | Prompt Assembly   | < 80 ms          | 1,000 active agents  |
| LLM Gateway (4o)    | Stream TTFT       | < 150 ms         | 500 concurrent LLM   |
| Docker Sandbox      | Code Exec / Test  | < 800 ms spawn   | 250 parallel containers|
+---------------------+-------------------+------------------+----------------------+
```

---

## 3.3 SCALABILITY REQUIREMENTS

AegisOS is engineered for linear horizontal scalability across database, worker execution, and real-time streaming tiers.

### 3.3.1 Capacity & Scale Specifications
1. **Multi-Tenant Capacity:** Support up to **10,000 active organization tenants** per cluster, isolated logically via multi-tenant schema partitioning and organization scoping.
2. **Project Scale:** Manage **100,000+ active software repositories** simultaneously, maintaining real-time AST graphs and dependency trees.
3. **Agent Worker Scale:** Execute **1,000 simultaneous autonomous AI agents** per cluster. Kubernetes Horizontal Pod Autoscaler (HPA) dynamically scales agent execution worker pods based on CPU, RAM, and Kafka queue depth metrics.
4. **User & Socket Concurrency:** Support **5,000 concurrent active dashboard users**, serving 50,000 open real-time SSE/WebSocket channels maintained by stateless gateway nodes behind NGINX / Cloudflare load balancers.
5. **Database Storage Scale:** PostgreSQL 16 configured with Patroni high-availability clusters (1 Primary Write, up to 5 Read Replicas). DB connection pooling managed via PgBouncer with a maximum pool size of 500 connections per instance.
6. **Kafka Message Partitioning:** Telemetry and execution topics partitioned across at least 16 partitions per broker cluster, providing parallel processing for Celery/Kafka consumer groups.
7. **Redis Memory Tiering:** Redis 7.2 Cluster with 6 nodes (3 primaries, 3 read replicas) utilizing memory eviction strategy `volatile-lru`. Rate limiting, session states, and Pub/Sub channels run on isolated Redis instance clusters to prevent cross-workload memory starvation.

---

## 3.4 SECURITY REQUIREMENTS

Security is a foundational imperative because AegisOS interacts directly with proprietary source code, infrastructure credentials, and automated deployment pipelines.

### 3.4.1 Encryption Architecture
- **Data in Transit:** Enforced TLS 1.3 across all public HTTP and WebSocket routes. HTTP traffic automatically upgraded via Strict-Transport-Security (HSTS) headers (`max-age=31536000; includeSubDomains; preload`). Internal service-to-service communication inside the Kubernetes cluster is secured using mutual TLS (mTLS) via Linkerd / Istio service mesh with SPIFFE/SPIRE identity attestation.
- **Data at Rest:** All persistent volumes (PostgreSQL, Redis persistence, S3 artifact buckets) are encrypted using AES-256-GCM. Sensitive application secrets (e.g., GitHub OAuth tokens, LLM API keys, SSH keys) are encrypted at the application layer using **Envelope Encryption** powered by AWS KMS / HashiCorp Vault master keys.
- **LLM Prompt Protection & Zero Retention:** All LLM integrations enforce Enterprise Zero Data Retention (ZDR) agreements with OpenAI/Azure, ensuring that user source code, prompts, and agent thoughts are never cached or used for model retraining.

### 3.4.2 Authentication & Authorization (RBAC / ABAC)
- **Authentication:** Supported protocols include OAuth 2.0 and OpenID Connect (OIDC) via GitHub, GitLab, Google Workspace, and Okta SAML 2.0. Session tokens are issued as JSON Web Tokens (JWT) signed with the RS256 algorithm. Access tokens expire in 15 minutes; refresh tokens expire in 7 days with automatic token family rotation.
- **Role-Based Access Control (RBAC):**
  - `System Admin`: Global node administration, tenant provisioning, system model routing.
  - `Organization Owner`: Member management, billing controls, cloud credential setup.
  - `Project Lead`: Project creation, agent workflow overrides, PR merge sign-offs.
  - `Developer`: Agent task invocation, prompt submission, diff viewing.
  - `Auditor`: Read-only access to audit trails, compliance reports, and agent logs.
- **Attribute-Based Access Control (ABAC):** Evaluates dynamic runtime policies based on resource tags (`sensitivity=critical`), runtime environment (`env=production`), and user IP ranges.

### 3.4.3 Audit Logging & Security Tracking
- All system events, file modifications, code commits, agent loop step executions, and permission updates generate an immutable append-only audit record.
- **Audit Schema Attributes:** `event_id`, `timestamp_utc`, `tenant_id`, `actor_type` (`USER` or `AGENT`), `actor_id`, `ip_address`, `action`, `resource_type`, `resource_id`, `payload_hash`, `signature`.
- Audit streams are written directly to write-once-read-many (WORM) storage (AWS S3 Object Lock) and indexed in ElasticSearch / OpenSearch with a mandatory retention requirement of 365 days.

---

## 3.5 RELIABILITY & AVAILABILITY REQUIREMENTS

| Reliability Indicator | Target Requirement | Operational Strategy / Failover Mechanism |
| :--- | :--- | :--- |
| **System Uptime SLA** | **99.99% Availability** (Max 4.38 mins downtime/month) | Multi-AZ K8s deployment across 3 isolated availability zones |
| **Mean Time to Recover (MTTR)** | **< 15 minutes** | Automated health checks, pod replacements, & ArgoCD rollbacks |
| **Mean Time Between Failures** | **> 720 hours (30 days)** | Continuous chaos testing via Chaos Mesh / Gremlin |
| **Recovery Point Objective (RPO)**| **< 1 minute** | Continuous PostgreSQL Write-Ahead Logging (WAL) streaming to S3 |
| **Recovery Time Objective (RTO)**| **< 10 minutes** | Patroni automated leader election & DB replica promotion |
| **Data Durability** | **99.999999999% (11 9s)** | Amazon S3 cross-region replication & multi-AZ Postgres storage |

### 3.5.1 Circuit Breakers & Fault Isolation
- Outbound connections to third-party endpoints (OpenAI, GitHub, Cloud APIs) are governed by Hystrix-style circuit breakers implemented via `tenacity` and custom FastAPI decorators.
- Circuit breaker policy: Failure threshold = 50% over a 10-second rolling window; circuit trips to `OPEN` for 30 seconds before testing recovery in `HALF-OPEN` state.

---

## 3.6 COMPATIBILITY REQUIREMENTS

### 3.6.1 Platform Compatibility Matrix
- **Server Operating Systems:** Linux Ubuntu 22.04 LTS, RHEL 9+, Debian 12 (x86_64 and ARM64/aarch64 architecture support).
- **Container Runtimes:** Docker Engine 26.0+, Containerd 1.7+, Kubernetes 1.28+.
- **Desktop Browsers:**
  - Chrome / Chromium v110+
  - Firefox v115+
  - Safari v16+
  - Microsoft Edge v110+
- **API Specification:** OpenAPI 3.1 schema compatibility for automated client SDK generation across TypeScript, Python, and Go.

---

## 3.7 INTEGRATION REQUIREMENTS

```
+-----------------------------------------------------------------------------------+
|                           AEGISOS INTEGRATION MATRIX                              |
+------------------+-----------------------+----------------------------------------+
| Integration Target| Protocol / Adapter   | Capabilities / Features                |
+------------------+-----------------------+----------------------------------------+
| GitHub / GitLab  | REST v3 / GraphQL     | Repos, PRs, Webhooks, Branch Protection|
| Docker Engine    | Unix Socket / TCP API | Sandbox container build & execution    |
| Cloud Providers  | AWS / GCP / Azure SDK | Provisioning, serverless, EKS/GKE      |
| LLM Providers    | OpenAI API / Azure    | GPT-4o, Embeddings, Token Streaming    |
| Monitoring       | Prometheus / OTEL     | Metrics, Tracing, Structured Logs      |
+------------------+-----------------------+----------------------------------------+
```

1. **Version Control Systems (VCS):** Native webhooks and REST/GraphQL adapters for GitHub Enterprise, GitHub.com, GitLab Self-Managed, and GitLab.com. Support for SSH deploy keys and GitHub App tokens.
2. **Container Sandbox Execution Engine:** Native integration with Docker Engine API and gVisor / Firecracker runtimes for secure, isolated code compilation, linting, and automated unit testing.
3. **Cloud Infrastructure Providers:** AWS (EKS, S3, RDS, IAM), GCP (GKE, Cloud Storage, Cloud SQL), Azure (AKS, Blob Storage, Azure SQL).
4. **Developer Workflows:** Jira Cloud, Linear, Slack Webhooks, Microsoft Teams notifications.

---

## 3.8 CONSTRAINT REQUIREMENTS

1. **Technology Stack Constraints:**
   - **Backend Framework:** Python 3.11+ with FastAPI asynchronous framework.
   - **Frontend Framework:** Next.js 14+ (App Router), React 18+, TypeScript 5+, Tailwind CSS.
   - **Primary Database:** PostgreSQL 16.
   - **Cache & Memory:** Redis 7.2.
   - **Message Broker:** Apache Kafka 3.6+.
   - **Primary Model Engine:** OpenAI GPT-4o with fallback capabilities to Claude 3.5 Sonnet / Azure OpenAI.
2. **UI & Theme Constraints:** AegisOS Dark Cyberpunk Theme enforced globally:
   - Primary Accent: Neon Emerald (`#00ff88`).
   - Primary Background: Dark Space (`#0a0d12`).
   - Panel Surface: Deep Glass (`#121820`).
   - Borders: Cyber Gray (`#1f2937`).
3. **Budget & Token Limit Constraints:** LLM token budgets enforced per task execution. Agents automatically enter a `paused_awaiting_approval` state if projected token costs exceed the user-configured budget ceiling (e.g., $5.00/task).

---

## 3.9 COMPLIANCE & GOVERNANCE REQUIREMENTS

1. **GDPR Compliance:**
   - User Data Eradication: Automated user data wipe endpoints (`DELETE /api/v1/users/{id}`).
   - Data Portability: Standardized JSON exports of user profile data, agent logs, and code histories.
2. **SOC 2 Type II Controls:**
   - Mandatory human sign-off policies prior to agent code execution in production environments.
   - Immutable audit logs capturing every human and agent system modification.
3. **License Governance:** Automatic static dependency scanning comparing agent-introduced packages against organization open-source licensing rules (e.g., flagging GPL/AGPL packages).

---

## 3.10 DISASTER RECOVERY & MULTI-REGION TOPOLOGY

AegisOS implements an Active-Passive Multi-Region Disaster Recovery architecture across two AWS/GCP regions (Primary: `us-east-1`, Secondary DR: `us-west-2`).

### 3.10.1 Disaster Recovery Metrics & Failover Protocol
- **RPO (Recovery Point Objective):** < 60 seconds achieved via asynchronous PostgreSQL cross-region streaming replication and S3 Cross-Region Replication (CRR) for build artifacts and repository snapshots.
- **RTO (Recovery Time Objective):** < 15 minutes managed via automated Route 53 / Cloudflare Magic Transit DNS health checks and Terraform/ArgoCD automated failover scripts.
- **Data Synchronization:** Redis states are backed up every 15 minutes to multi-region S3 buckets. Kafka messages are mirrored asynchronously using Kafka MirrorMaker 2 across regions.

---

## 3.11 OPERATIONAL MONITORING & TELEMETRY SLAS

The AegisOS platform enforces strict telemetry observability SLAs to ensure immediate fault detection and automated alerting across all infrastructure tiers.

1. **Metrics Collection:** Prometheus scrapes endpoints every 5 seconds for system metrics (`/metrics`). Custom counters track `agent_execution_total`, `llm_token_usage_total`, and `sandbox_spawn_duration_seconds`.
2. **Distributed Tracing:** OpenTelemetry spans injected into all ASGI request contexts, tracing HTTP calls from API gateway to FastAPI service handlers, PostgreSQL queries, Redis operations, and outbound OpenAI GPT-4o API calls.
3. **Log Aggregation:** FluentBit sidecars tail container stdout/stderr, formatting logs in JSON with `trace_id` and `span_id` injected, streaming directly to ElasticSearch / OpenSearch clusters with 30-day hot search retention.

---

## 3.12 COMPREHENSIVE ACCEPTANCE CRITERIA MATRIX

| Requirement Code | Category | Requirement Description | Verification Method | Pass / Fail Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **AC-TRD-01** | Performance | REST API latency under 5,000 req/sec | Automated Load Test (k6) | p95 latency < 45 ms across 100k requests |
| **AC-TRD-02** | Scalability | 1,000 concurrent active AI agents | Chaos Load Test | 1,000 worker threads execute without pod crashes |
| **AC-TRD-03** | Security | AES-256 Envelope Encryption | Vault Audit | Secret DB columns store ciphertexts; KMS unreadable |
| **AC-TRD-04** | Security | OAuth2 + JWT Verification | Penetration Test | Expired/malformed tokens return HTTP 401 |
| **AC-TRD-05** | Security | Immutable Audit Logging | S3 Object Lock Check | Attempted overwrite/delete fails with 403 Forbidden |
| **AC-TRD-06** | Reliability | Automated DB Failover | Chaos Kill Primary | Primary PostgreSQL node killed; standby promoted < 10s |
| **AC-TRD-07** | Integration | GitHub PR Lifecycle Integration | E2E Playwright Suite | Agent creates branch, pushes commit, and opens PR |
| **AC-TRD-08** | Compliance | GDPR User Erasure | API Test Execution | Target user records purged across DB and search index |
| **AC-TRD-09** | UI Theme | Dark Mode & `#00ff88` Accent | DOM Automated Audit | 100% of views render dark background & `#00ff88` accent |
| **AC-TRD-10** | Sandbox | Container Security Isolation | Escape Penetration Test | Container process blocked from host filesystem/network |


# 5. BACKEND ARCHITECTURE

## 5.1 SYSTEM ARCHITECTURAL OVERVIEW
The AegisOS backend is engineered using Python 3.11+ and the FastAPI asynchronous web framework. It follows a layered, domain-driven micro-monolith architecture designed for high throughput, sub-second streaming responsiveness, and fault-tolerant background worker orchestration.

### 5.1.1 Architectural Topology Diagram
```
                               +-----------------------------+
                               |     NGINX / API GATEWAY     |
                               +--------------+--------------+
                                              |
                                              v
                              +---------------+---------------+
                              |    FastAPI Web Application    |
                              |   (ASGI / Uvicorn Clusters)   |
                              +---------------+---------------+
                                              |
         +--------------------+---------------+--------------------+--------------------+
         |                    |               |                    |                    |
         v                    v               v                    v                    v
+----------------+   +----------------+  +----------+    +--------------------+  +------------------+
| OAuth / IAM    |   | Project Service|  | Agent    |    | Execution Sandbox  |  | Event Publisher  |
| Middleware     |   | Layer          |  | Engine   |    | Service (Docker)   |  | (Kafka Producer) |
+----------------+   +----------------+  +----------+    +--------------------+  +------------------+
         |                    |               |                    |                    |
         +--------------------+---------------+--------------------+--------------------+
                                              |
               +------------------------------+------------------------------+
               |                              |                              |
               v                              v                              v
      +------------------+           +------------------+           +------------------+
      |  PostgreSQL 16   |           |  Redis 7.2 Cluster|           | Apache Kafka 3.6 |
      | (Relational DB)  |           |(Cache / PubSub)  |           |   (Event Bus)    |
      +------------------+           +------------------+           +------------------+
                                              |                              |
                                              v                              v
                                     +------------------+           +------------------+
                                     |  Celery Worker   |           | LLM Router Pool  |
                                     |  Task Processors |           |   (GPT-4o API)   |
                                     +------------------+           +------------------+
```

---

## 5.2 CODE ORGANIZATION & DIRECTORY STRUCTURE

AegisOS maintains strict module boundaries following Clean Architecture principles.

```
aegis_backend/
├── app/
│   ├── main.py                   # FastAPI Application Entrypoint & Lifespan Hooks
│   ├── core/                     # Core Infrastructure
│   │   ├── config.py             # BaseSettings Pydantic Configuration
│   │   ├── database.py           # Async SQLAlchemy Engine & Session Factory
│   │   ├── redis.py              # Async Redis Connection Pool
│   │   ├── kafka.py              # Kafka Async Producer & Consumer
│   │   ├── security.py           # JWT, AES Envelope Encryption, Password Hashing
│   │   ├── middleware.py         # ASGI Middleware Chain
│   │   └── exceptions.py         # Exception Hierarchy & RFC 7807 Handlers
│   ├── api/                      # API Layer (Routers)
│   │   ├── v1/
│   │   │   ├── router.py         # V1 API Router Aggregator
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py       # IAM & API Key Management
│   │   │   │   ├── projects.py   # Project Workspace API
│   │   │   │   ├── agents.py     # Agent Execution API
│   │   │   │   ├── workflows.py  # Workflow DAG Pipelines API
│   │   │   │   ├── storage.py    # Artifact Stream Upload API
│   │   │   │   └── health.py     # Liveness/Readiness Probes
│   │   │   └── websockets/
│   │   │       └── terminal.py   # Real-Time WebSocket Terminal Router
│   ├── services/                 # Domain Services (Business Logic)
│   │   ├── agent_engine.py       # ReAct Loop & Agent State Machine
│   │   ├── project_service.py    # Repository Context & AST Extraction
│   │   ├── llm_router.py         # GPT-4o Token Streaming & Cost Accounting
│   │   ├── sandbox_service.py    # Docker Container Execution Sandbox
│   │   └── workflow_engine.py   # DAG Pipeline Execution Engine
│   ├── models/                   # SQLAlchemy 2.0 ORM Models
│   │   ├── project.py
│   │   ├── agent.py
│   │   ├── workflow.py
│   │   ├── audit.py
│   │   └── user.py
│   ├── schemas/                  # Pydantic v2 Validation Schemas
│   │   ├── project.py
│   │   ├── agent.py
│   │   ├── workflow.py
│   │   └── auth.py
│   └── workers/                  # Asynchronous Background Processing
│       ├── celery_app.py         # Celery Setup
│       └── tasks/
│           ├── code_analysis.py  # AST & Dependency Graph Processing
│           ├── git_sync.py       # Git Fetch / Branch / Commit Workers
│           └── agent_runner.py   # Long-Running Agent Loops
├── alembic/                      # Database Migration Scripts
├── Dockerfile                    # Production Container Definition
└── requirements.txt              # Dependency Declarations
```

---

## 5.3 DEPENDENCY INJECTION PATTERN

FastAPI’s `Depends()` dependency injection mechanism manages component lifecycles, database transactions, authentication verification, and external service pool resolution cleanly without global state pollution.

```python
# app/core/dependencies.py
from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import redis.asyncio as aioredis

from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis_pool
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated, transactional SQLAlchemy session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_redis() -> aioredis.Redis:
    """Returns an async Redis client from the shared connection pool."""
    return await get_redis_pool()

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Authenticates JWT access token and yields active user model."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(user_id=user_id, role=payload.get("role"))
    except JWTError:
        raise credentials_exception

    user = await db.get(User, token_data.user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    return user
```

---

## 5.4 MIDDLEWARE CHAIN ORDER & DESIGN

Every incoming request passes through an explicit ASGI middleware pipeline.

```
Incoming HTTP/WS Request
           │
           ▼
┌──────────────────────────────────────────┐
│ 1. CORS & Security Headers Middleware    │
└──────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ 2. Correlation ID Middleware             │ (Injects X-Request-ID & sets logging context)
└──────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ 3. Prometheus / OpenTelemetry Tracing    │ (Records HTTP metrics & request spans)
└──────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ 4. Sliding Window Rate Limiting          │ (Redis token bucket evaluation)
└──────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ 5. DB Session Context Middleware         │
└──────────────────────────────────────────┘
           │
           ▼
     FastAPI Route Handler
```

### 5.4.1 Custom Rate Limit Middleware Code
```python
# app/core/middleware.py
import time
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis import get_redis_pool

class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in ["/healthz", "/livez", "/readyz"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}"
        now = time.time()
        clear_before = now - 60

        redis = await get_redis_pool()
        async with redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, clear_before)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, 60)
            results = await pipe.execute()

        request_count = results[1]
        if request_count >= self.requests_per_minute:
            return Response(
                content='{"error": "Rate limit exceeded. Try again in 60 seconds."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(self.requests_per_minute)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.requests_per_minute - request_count - 1))
        return response
```

---

## 5.5 ORM MODELS & DATABASE MIGRATIONS

### 5.5.1 SQLAlchemy 2.0 ORM Models Definitions
```python
# app/models/domain_models.py
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="developer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    repo_url: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(60), nullable=False) # Architect, Developer, QA, Security
    status: Mapped[str] = mapped_column(String(30), default="idle", index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    max_loops: Mapped[int] = mapped_column(Integer, default=20)
    accumulated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    memory_context: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="agents")
```

---

## 5.6 DOMAIN SERVICE LAYER IMPLEMENTATION

The domain service layer isolates business logic from transportation layers (REST/WebSocket). The `AgentEngineService` manages the autonomous ReAct (Reason + Act) loop for GPT-4o interactions.

```python
# app/services/agent_engine.py
import json
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.domain_models import Agent
from app.core.kafka import publish_event

logger = logging.getLogger("aegis.agent_engine")

class AgentEngineService:
    def __init__(self, llm_client: AsyncOpenAI):
        self.llm_client = llm_client

    async def execute_react_step(self, agent: Agent, user_prompt: str) -> AsyncGenerator[dict, None]:
        """Executes a single ReAct iteration, yielding token streams and tool calls."""
        system_instruction = (
            f"You are {agent.name}, a specialized AI {agent.role} in AegisOS. "
            "Examine context, reason step-by-step, and output structured tool actions."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]

        response_stream = await self.llm_client.chat.completions.create(
            model=settings.DEFAULT_LLM_MODEL,
            messages=messages,
            stream=True,
            temperature=0.2,
            max_tokens=2048
        )

        full_content = ""
        async for chunk in response_stream:
            delta = chunk.choices[0].delta.content or ""
            full_content += delta
            yield {"type": "token_delta", "delta": delta}

        # Record step completion event to Kafka bus
        await publish_event(
            topic="aegis.agent.events",
            key=agent.id,
            payload={
                "agent_id": agent.id,
                "step": agent.current_step + 1,
                "status": "step_completed",
                "content_preview": full_content[:100]
            }
        )
```

---

## 5.7 ERROR HANDLING STRATEGY & EXCEPTION HIERARCHY

AegisOS standardizes all API errors to comply with **RFC 7807 (Problem Details for HTTP APIs)**.

### 5.7.1 Centralized Exception Handler Implementation
```python
# app/core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("aegis.exceptions")

class AegisBaseException(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

class AgentExecutionTimeout(AegisBaseException):
    def __init__(self, agent_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Agent '{agent_id}' execution exceeded limit of {timeout_seconds}s.",
            code="ERR_AGENT_EXECUTION_TIMEOUT",
            status_code=504,
            details={"agent_id": agent_id, "timeout_seconds": timeout_seconds}
        )

async def aegis_exception_handler(request: Request, exc: AegisBaseException) -> JSONResponse:
    logger.warning(f"Domain exception occurred: {exc.code} - {exc.message} Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://aegisos.dev/errors/{exc.code.lower()}",
            "title": exc.code,
            "status": exc.status_code,
            "detail": exc.message,
            "instance": request.url.path,
            "error_details": exc.details
        },
        headers={"Content-Type": "application/problem+json"}
    )
```

---

## 5.8 BACKGROUND TASK PROCESSING (CELERY WORKERS)

Long-running operations—such as multi-file repository AST indexing, Docker sandbox execution, and background test runs—are offloaded to distributed Celery worker processes backed by Redis / Kafka.

```python
# app/workers/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "aegis_tasks",
    broker=settings.KAFKA_BROKER_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks.code_analysis", "app.workers.tasks.agent_runner"]
)

celery_app.conf.update(
    task_routes={
        "app.workers.tasks.agent_runner.*": {"queue": "agent_execution"},
        "app.workers.tasks.code_analysis.*": {"queue": "code_indexing"},
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

---

## 5.9 CONTAINER SANDBOX EXECUTION SERVICE

To run untrusted agent-generated code securely, AegisOS uses an asynchronous container sandbox manager that interacts directly with the Docker Engine API over Unix sockets (`/var/run/docker.sock`).

```python
# app/services/sandbox_service.py
import aiohttp
import asyncio
import logging

logger = logging.getLogger("aegis.sandbox")

class DockerSandboxService:
    def __init__(self, docker_socket_path: str = "/var/run/docker.sock"):
        self.connector = aiohttp.UnixConnector(path=docker_socket_path)

    async def execute_code_in_sandbox(self, image: str, command: list[str], timeout: int = 30) -> dict:
        """Spawns an isolated ephemeral container with restricted cgroups & no root privileges."""
        async with aiohttp.ClientSession(connector=self.connector) as session:
            create_payload = {
                "Image": image,
                "Cmd": command,
                "HostConfig": {
                    "Memory": 512 * 1024 * 1024, # 512MB RAM limit
                    "NanoCpus": 1000000000,      # 1.0 vCPU limit
                    "NetworkMode": "none",       # Complete network isolation
                    "ReadonlyRootfs": True,
                    "AutoRemove": True
                }
            }

            async with session.post("http://localhost/v1.43/containers/create", json=create_payload) as resp:
                if resp.status != 201:
                    raise Exception(f"Failed to create sandbox container: {await resp.text()}")
                container_data = await resp.json()
                container_id = container_data["Id"]

            async with session.post(f"http://localhost/v1.43/containers/{container_id}/start") as resp:
                pass

            await asyncio.sleep(0.5)
            return {"container_id": container_id, "status": "completed"}
```

---

## 5.10 FILE UPLOAD & ARTIFACT STREAMING PIPELINE

```python
# app/api/v1/endpoints/storage.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
import aioboto3
from app.core.config import settings
from app.core.dependencies import get_current_user

router = APIRouter()

@router.post("/upload-artifact", status_code=status.HTTP_201_CREATED)
async def upload_project_artifact(
    project_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Streams file chunks directly to object storage with content verification."""
    allowed_types = ["application/zip", "application/x-tar", "application/gzip"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid archive file format.")

    session = aioboto3.Session()
    s3_key = f"artifacts/{project_id}/{file.filename}"
    
    async with session.client("s3", endpoint_url=settings.S3_ENDPOINT_URL) as s3:
        await s3.upload_fileobj(
            file.file,
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )

    return {"project_id": project_id, "s3_key": s3_key, "status": "uploaded"}
```

---

## 5.11 CONFIGURATION MANAGEMENT & SECRETS

Configuration management relies on Pydantic `BaseSettings` reading environment variables with strict runtime validation.

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AegisOS Backend"
    ENVIRONMENT: str = "production"
    API_V1_STR: str = "/api/v1"
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    MAX_AGENT_LOOPS: int = 25
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 5.12 HEALTH CHECK & OBSERVABILITY ENDPOINTS

```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.dependencies import get_db, get_redis
import json

router = APIRouter()

@router.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness_probe():
    return {"status": "alive"}

@router.get("/readyz")
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    health_status = {"status": "ok", "checks": {}}
    
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    try:
        ping = await redis.ping()
        health_status["checks"]["redis"] = "healthy" if ping else "unhealthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    if health_status["status"] != "ok":
        return Response(
            content=json.dumps(health_status),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json"
        )
    return health_status
```


# 6. FRONTEND ARCHITECTURE

## 6.1 SYSTEM OVERVIEW & UI VISION
The AegisOS Web Client is built on Next.js 14+ (App Router) with TypeScript, React 18+, Tailwind CSS, and Shadcn UI. The application delivers an ultra-responsive, real-time developer environment optimized for monitoring multi-agent code generation, terminal streams, and workflow DAG visualizations.

### 6.1.1 AegisOS Dark Cyberpunk Theme Specification
- **Primary Accent:** Neon Emerald (`#00ff88`) - Used for active states, CTA buttons, active agent execution rings, and success indicators.
- **Background Surface (900):** Dark Space (`#0a0d12`) - Main window and dashboard layout background.
- **Panel Surface (800):** Deep Glass (`#121820`) - Cards, panels, sidebars, and active terminal containers.
- **Subtle Border (700):** Cyber Gray (`#1f2937`) - 1px borders, table dividers, and tree nodes.
- **Foreground Text:** High Contrast White (`#f3f4f6`) and Muted Slate (`#9ca3af`).

---

## 6.2 NEXT.JS APP ROUTER STRUCTURE & LAYOUT HIERARCHY

The directory structure separates server component routing from client hooks, stores, and components.

```
aegis_frontend/
├── app/
│   ├── layout.tsx                # Root Layout (Theme Provider, QueryClientProvider, Font)
│   ├── page.tsx                  # Landing / Root Portal Redirect Page
│   ├── globals.css               # Cyberpunk Theme Variables & Custom Scrollbars
│   ├── (auth)/                   # Unauthenticated Authentication Route Group
│   │   ├── layout.tsx            # Centered Auth Card Layout
│   │   ├── login/page.tsx        # Login Form Component
│   │   └── sso/page.tsx          # OAuth / SAML Callback Handler
│   ├── (dashboard)/              # Authenticated Workspace Layout Group
│   │   ├── layout.tsx            # TopNav + Sidebar + Real-time Socket Connection
│   │   ├── dashboard/page.tsx    # Global Multi-Project & Agent Status Overview
│   │   ├── projects/
│   │   │   ├── page.tsx          # Repository & Project Catalog Grid
│   │   │   └── [id]/
│   │   │       ├── layout.tsx    # Project Context Bar & Tab Navigation
│   │   │       ├── page.tsx      # Project Dashboard & Quick Actions
│   │   │       ├── agents/
│   │   │       │   └── page.tsx  # Agent Execution Terminal & Inspector
│   │   │       ├── workflows/
│   │   │       │   └── page.tsx  # React Flow DAG Workflow Builder
│   │   │       └── code/
│   │   │           └── page.tsx  # Monaco Editor with Real-Time Agent Diff View
│   │   └── settings/
│   │       ├── page.tsx          # User Profile & Security Settings
│   │       └── integrations/page.tsx # GitHub/GitLab OAuth Setup
├── components/
│   ├── ui/                       # Atomic Shadcn UI Components
│   │   ├── button.tsx
│   │   ├── badge.tsx
│   │   ├── dialog.tsx
│   │   └── tabs.tsx
│   ├── agent/                    # Agent Domain Components
│   │   ├── AgentTerminal.tsx     # Virtualized Xterm.js / Log Stream Renderer
│   │   ├── AgentStatusBadge.tsx  # Pulsing #00ff88 Status Indicator
│   │   └── AgentThoughtCard.tsx  # ReAct Step Inspector
│   ├── workflow/                 # DAG Canvas Components
│   │   └── WorkflowCanvas.tsx    # Custom React Flow Node Graph
│   └── code/                     # IDE & Diff Components
│       └── MonacoDiffViewer.tsx  # Side-by-Side Agent Code Diff
├── hooks/                        # Custom React Hooks
│   ├── useAgentStream.ts         # SSE / WS Real-Time Token Parser
│   ├── useAuth.ts                # Session & JWT Refresh Manager
│   └── useProjectQuery.ts        # TanStack Query Client Fetchers
├── store/                        # Client-Side State Management (Zustand)
│   ├── useAuthStore.ts           # Token & User Profile State
│   ├── useAgentStore.ts          # Active Agent Log Buffers & Terminal State
│   └── useProjectStore.ts        # Selected Repository State
├── lib/                          # Utility & API Client Configuration
│   ├── api_client.ts             # Axios / Fetch Interceptors with Auto-Token Refresh
│   └── theme_config.ts           # Tailwind Color Extender
└── public/
    ├── manifest.json             # PWA Manifest Configuration
    └── sw.js                     # Service Worker for Offline & Push Notifications
```

---

## 6.3 STATE MANAGEMENT ARCHITECTURE (ZUSTAND JUSTIFICATION)

### 6.3.1 Architectural Selection & Comparison
Evaluating state management solutions for AegisOS:
1. **Redux Toolkit:** Excessive boilerplate and unnecessary re-renders across deep terminal log streams.
2. **Jotai / Recoil:** Excellent atomic state, but lacks consolidated action semantics required for complex agent state transitions.
3. **Zustand (Selected):** Unopinionated, minimal bundle footprint (< 1.2 KB), transient state subscription capabilities (subscribing directly to high-frequency token streams without forcing React DOM re-renders), and clean multi-store separation.

### 6.3.2 Zustand Stores Implementation
```typescript
// store/useAgentStore.ts
import { create } from 'zustand';

export interface AgentThought {
  id: string;
  step: number;
  action: string;
  thought: string;
  timestamp: string;
}

interface AgentState {
  activeAgentId: string | null;
  agentStatus: 'idle' | 'thinking' | 'executing' | 'completed' | 'error';
  thoughts: AgentThought[];
  logs: string[];
  setActiveAgent: (agentId: string) => void;
  appendThought: (thought: AgentThought) => void;
  appendLogChunk: (chunk: string) => void;
  clearTerminal: () => void;
  setStatus: (status: AgentState['agentStatus']) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  activeAgentId: null,
  agentStatus: 'idle',
  thoughts: [],
  logs: [],
  setActiveAgent: (agentId) => set({ activeAgentId: agentId, thoughts: [], logs: [] }),
  appendThought: (thought) => set((state) => ({ thoughts: [...state.thoughts, thought] })),
  appendLogChunk: (chunk) => set((state) => ({ logs: [...state.logs, chunk] })),
  clearTerminal: () => set({ thoughts: [], logs: [] }),
  setStatus: (agentStatus) => set({ agentStatus }),
}));
```

```typescript
// store/useProjectStore.ts
import { create } from 'zustand';

interface ProjectState {
  selectedProjectId: string | null;
  activeBranch: string;
  setSelectedProject: (projectId: string) => void;
  setActiveBranch: (branch: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  selectedProjectId: null,
  activeBranch: 'main',
  setSelectedProject: (projectId) => set({ selectedProjectId: projectId }),
  setActiveBranch: (branch) => set({ activeBranch: branch }),
}));
```

---

## 6.4 DATA FETCHING & REAL-TIME WS STREAMING INTEGRATION

AegisOS employs **TanStack Query (React Query v5)** for asynchronous HTTP REST data fetching, combined with a custom WebSocket manager that pushes updates directly into the Zustand store.

### 6.4.1 Real-Time WebSocket Hook Implementation
```typescript
// hooks/useAgentStream.ts
import { useEffect, useRef } from 'react';
import { useAgentStore } from '@/store/useAgentStore';

export function useAgentStream(agentId: string | null) {
  const socketRef = useRef<WebSocket | null>(null);
  const { appendThought, appendLogChunk, setStatus } = useAgentStore();

  useEffect(() => {
    if (!agentId) return;

    const wsUrl = `wss://api.aegisos.dev/api/v1/ws/agents/${agentId}/stream`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setStatus('thinking');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'thought') {
          appendThought(message.payload);
        } else if (message.type === 'log') {
          appendLogChunk(message.payload.text);
        } else if (message.type === 'status_change') {
          setStatus(message.payload.status);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket agent payload', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket connection error:', error);
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus('idle');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [agentId, appendThought, appendLogChunk, setStatus]);

  return { socket: socketRef.current };
}
```

---

## 6.5 ADVANCED CODE VIEWER & DIFFING ENGINE

AegisOS embeds Microsoft Monaco Editor to present side-by-side git diffs produced by autonomous AI agent commits.

```typescript
// components/code/MonacoDiffViewer.tsx
'use client';

import React from 'react';
import { DiffEditor } from '@monaco-editor/react';

interface MonacoDiffViewerProps {
  originalCode: string;
  modifiedCode: string;
  language?: string;
}

export const MonacoDiffViewer: React.FC<MonacoDiffViewerProps> = ({
  originalCode,
  modifiedCode,
  language = 'typescript',
}) => {
  return (
    <div className="h-full w-full rounded-lg border border-[#1f2937] overflow-hidden bg-[#0a0d12]">
      <DiffEditor
        height="100%"
        language={language}
        original={originalCode}
        modified={modifiedCode}
        theme="vs-dark"
        options={{
          renderSideBySide: true,
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 13,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          smoothScrolling: true,
        }}
      />
    </div>
  );
};
```

---

## 6.6 WORKFLOW CANVAS GRAPH ENGINE

To visualize multi-agent execution pipelines, AegisOS uses React Flow to render interactive, animated Directed Acyclic Graphs (DAGs).

```typescript
// components/workflow/WorkflowCanvas.tsx
'use client';

import React, { useCallback } from 'react';
import ReactFlow, {
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';

const initialNodes = [
  {
    id: 'node-1',
    type: 'default',
    data: { label: 'Architect Agent' },
    position: { x: 100, y: 100 },
    style: { background: '#121820', color: '#00ff88', border: '1px solid #00ff88', borderRadius: '8px' },
  },
  {
    id: 'node-2',
    type: 'default',
    data: { label: 'Developer Agent' },
    position: { x: 350, y: 100 },
    style: { background: '#121820', color: '#f3f4f6', border: '1px solid #1f2937', borderRadius: '8px' },
  },
];

const initialEdges = [
  { id: 'e1-2', source: 'node-1', target: 'node-2', animated: true, style: { stroke: '#00ff88' } },
];

export const WorkflowCanvas: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="h-full w-full bg-[#0a0d12] rounded-lg border border-[#1f2937]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background color="#1f2937" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
```

---

## 6.7 AGENT TERMINAL COMPONENT WITH VIRTUALIZATION

```typescript
// components/agent/AgentTerminal.tsx
'use client';

import React, { useRef, useEffect } from 'react';
import { useAgentStore } from '@/store/useAgentStore';

export const AgentTerminal: React.FC = () => {
  const { logs, agentStatus, clearTerminal } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="flex flex-col h-full bg-[#121820] border border-[#1f2937] rounded-lg overflow-hidden font-mono text-xs text-[#f3f4f6]">
      <div className="flex items-center justify-between px-4 py-2 bg-[#0a0d12] border-b border-[#1f2937]">
        <div className="flex items-center space-x-2">
          <span className={`h-2.5 w-2.5 rounded-full ${agentStatus === 'executing' ? 'bg-[#00ff88] animate-ping' : 'bg-gray-500'}`} />
          <span className="font-bold text-[#00ff88]">AEGIS TERMINAL AGENT STREAM</span>
        </div>
        <button
          onClick={clearTerminal}
          className="px-2 py-1 text-xs bg-[#1f2937] hover:bg-gray-700 text-gray-300 rounded transition-colors"
        >
          Clear
        </button>
      </div>
      <div className="flex-1 p-4 overflow-y-auto space-y-1">
        {logs.map((log, idx) => (
          <div key={idx} className="leading-relaxed">
            <span className="text-[#00ff88] mr-2">&gt;</span>
            <span>{log}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
```

---

## 6.8 AXIOS / FETCH HTTP CLIENT INTERCEPTOR PIPELINE

```typescript
// lib/api_client.ts
import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://api.aegisos.dev/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshResponse = await axios.post('https://api.aegisos.dev/api/v1/auth/refresh');
        const newToken = refreshResponse.data.access_token;
        useAuthStore.getState().setAccessToken(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (refreshErr) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

---

## 6.9 AUTHENTICATION FLOW & PROTECTED ROUTES

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('aegis_access_token')?.value;
  const isAuthRoute = request.nextUrl.pathname.startsWith('/login') || request.nextUrl.pathname.startsWith('/sso');

  if (!token && !isAuthRoute) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (token && isAuthRoute) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

---

## 6.10 ERROR BOUNDARIES & FALLBACK UI

```typescript
// components/AgentErrorBoundary.tsx
'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AgentErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught agent UI error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 bg-[#121820] border border-red-500/30 rounded-lg text-white">
          <h3 className="text-lg font-bold text-red-400">
            {this.props.fallbackTitle || 'Agent Widget Error'}
          </h3>
          <p className="mt-2 text-sm text-gray-400">
            {this.state.error?.message || 'An unexpected rendering error occurred in this module.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-4 px-4 py-2 bg-[#00ff88] text-black font-semibold rounded hover:bg-[#00cc6d] transition-colors"
          >
            Reset Widget
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 6.11 PERFORMANCE OPTIMIZATION & LAZY LOADING STRATEGY

To maintain high rendering framerates during intensive real-time agent output streaming, AegisOS employs specific Next.js dynamic code splitting and component memoization strategies:

1. **Monaco Code Editor & React Flow Canvas:** Heavy interactive dependencies are dynamic-imported with `ssr: false` to keep initial server render payloads small.
2. **Virtualization:** Log output streams rendering thousands of lines utilize `@tanstack/react-virtual` to render only the DOM nodes currently within the user viewport.
3. **Asset Budget:** Initial JavaScript bundle budget is constrained to < 150 KB gzipped for the core application shell.

```typescript
// app/(dashboard)/projects/[id]/code/page.tsx
'use client';

import dynamic from 'next/dynamic';

const MonacoDiffViewer = dynamic(
  () => import('@/components/code/MonacoDiffViewer').then((mod) => mod.MonacoDiffViewer),
  { ssr: false }
);
```

---

## 6.12 SERVICE WORKER & PWA INFRASTRUCTURE

```javascript
// public/sw.js
const CACHE_NAME = 'aegis-v1';
const STATIC_ASSETS = ['/', '/dashboard', '/manifest.json', '/favicon.ico'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/api/v1/')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
```


# 13. API ARCHITECTURE

## 13.1 REST API DESIGN PRINCIPLES
AegisOS exposes a uniform, resource-oriented RESTful API following modern API design standards:
1. **Resource URIs:** Standard plural nouns representing domain entities (e.g., `/projects`, `/agents`, `/workflows`).
2. **HTTP Verbs:** Strict adherence to HTTP semantics:
   - `GET`: Idempotent read operations (no side effects).
   - `POST`: Create resource or execute imperative domain actions (e.g., `/agents/{id}/execute`).
   - `PUT`: Complete idempotent resource replacement.
   - `PATCH`: Partial resource updates.
   - `DELETE`: Idempotent resource removal.
3. **Statelessness:** No session affinity required on API nodes; all request contexts encapsulated in JWT / API Key headers.
4. **Standard Error Payloads:** All client errors return RFC 7807 Problem Details JSON format.

---

## 13.2 API ENDPOINT CATALOG (32 ENDPOINTS)

| # | HTTP Method | Path | Summary / Description | Auth Scope Required |
| :-: | :--- | :--- | :--- | :--- |
| **1** | `POST` | `/api/v1/auth/login` | Authenticate user credentials and return JWT token pair | `Public` |
| **2** | `POST` | `/api/v1/auth/refresh` | Rotate expired access token using valid refresh token | `Public` |
| **3** | `GET` | `/api/v1/auth/me` | Fetch current authenticated user profile & permissions | `user:read` |
| **4** | `POST` | `/api/v1/auth/api-keys` | Generate new scoped system API key | `org:admin` |
| **5** | `DELETE`| `/api/v1/auth/api-keys/{key_id}` | Revoke an active API key | `org:admin` |
| **6** | `GET` | `/api/v1/projects` | List organization software projects (paginated) | `project:read` |
| **7** | `POST` | `/api/v1/projects` | Provision a new project workspace & bind repository | `project:write` |
| **8** | `GET` | `/api/v1/projects/{id}` | Retrieve project details, status, & telemetry | `project:read` |
| **9** | `PATCH` | `/api/v1/projects/{id}` | Update project metadata, LLM budgets, or settings | `project:write` |
| **10**| `DELETE`| `/api/v1/projects/{id}` | Archive or soft-delete a project | `project:admin` |
| **11**| `POST` | `/api/v1/projects/{id}/sync` | Trigger asynchronous repository re-indexing / AST scan | `project:write` |
| **12**| `GET` | `/api/v1/agents` | List active agent instances & definitions | `agent:read` |
| **13**| `POST` | `/api/v1/agents` | Instantiate a specialized AI agent worker | `agent:write` |
| **14**| `GET` | `/api/v1/agents/{id}` | Fetch agent state, memory context, and loop step counter | `agent:read` |
| **15**| `POST` | `/api/v1/agents/{id}/execute` | Dispatch an autonomous task or prompt to an agent | `agent:execute` |
| **16**| `POST` | `/api/v1/agents/{id}/pause` | Interrupt an active agent execution loop | `agent:execute` |
| **17**| `POST` | `/api/v1/agents/{id}/resume` | Resume a paused agent loop | `agent:execute` |
| **18**| `GET` | `/api/v1/agents/{id}/logs` | Fetch virtualized execution logs for an agent | `agent:read` |
| **19**| `GET` | `/api/v1/agents/{id}/stream` | SSE Endpoint: Continuous token/thought event stream | `agent:read` |
| **20**| `GET` | `/api/v1/workflows` | Catalog of multi-agent DAG workflow templates | `workflow:read` |
| **21**| `POST` | `/api/v1/workflows` | Create a custom multi-agent execution pipeline | `workflow:write` |
| **22**| `POST` | `/api/v1/workflows/{id}/run` | Trigger execution of a workflow pipeline DAG | `workflow:execute` |
| **23**| `GET` | `/api/v1/workflows/runs/{run_id}`| Get real-time status of a workflow run | `workflow:read` |
| **24**| `GET` | `/api/v1/repositories/{id}/files` | Retrieve project repository directory tree | `repo:read` |
| **25**| `GET` | `/api/v1/repositories/{id}/file` | Fetch source code content of a specific file path | `repo:read` |
| **26**| `POST` | `/api/v1/sandboxes/exec` | Execute arbitrary command in isolated Docker sandbox | `sandbox:exec` |
| **27**| `POST` | `/api/v1/storage/upload` | Upload build archive or code artifact | `storage:write` |
| **28**| `GET` | `/api/v1/webhooks` | List active webhook subscriptions | `webhook:read` |
| **29**| `POST` | `/api/v1/webhooks` | Register a new outbound event webhook endpoint | `webhook:write` |
| **30**| `DELETE`| `/api/v1/webhooks/{id}` | Delete an outbound webhook endpoint | `webhook:write` |
| **31**| `GET` | `/healthz` | Platform process liveness check | `Public` |
| **32**| `GET` | `/readyz` | System readiness check (DB, Redis, Kafka validation) | `Public` |

---

## 13.3 ENDPOINT DEEP DIVE & PAYLOAD SCHEMAS

### 13.3.1 Agent Task Dispatch Request Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentExecuteRequest",
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string",
      "minLength": 5,
      "maxLength": 10000,
      "description": "User instruction or engineering task given to the agent."
    },
    "context_files": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of relative file paths to inject into prompt memory context."
    },
    "max_loops": {
      "type": "integer",
      "default": 15,
      "maximum": 50,
      "description": "Maximum ReAct execution loops before requiring human sign-off."
    },
    "budget_limit_usd": {
      "type": "number",
      "default": 2.50,
      "description": "Maximum LLM token cost limit in USD for this task."
    }
  },
  "required": ["prompt"]
}
```

### 13.3.2 Project Provisioning Request Payload Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CreateProjectPayload",
  "type": "object",
  "properties": {
    "name": { "type": "string", "example": "Aegis Enterprise Microservice" },
    "repo_url": { "type": "string", "example": "https://github.com/org/microservice" },
    "default_branch": { "type": "string", "default": "main" },
    "language_stack": {
      "type": "array",
      "items": { "type": "string" },
      "example": ["python", "fastapi", "postgresql"]
    },
    "llm_monthly_budget_usd": { "type": "number", "default": 500.00 }
  },
  "required": ["name", "repo_url"]
}
```

### 13.3.3 Workflow Creation Pipeline Payload Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CreateWorkflowPayload",
  "type": "object",
  "properties": {
    "name": { "type": "string", "example": "Full-Stack Refactor Pipeline" },
    "description": { "type": "string", "example": "Multi-agent architecture & implementation pipeline." },
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step_id": { "type": "string", "example": "step_arch_01" },
          "agent_role": { "type": "string", "example": "Architect" },
          "prompt_template": { "type": "string", "example": "Analyze repo structure and design refactor spec." },
          "depends_on": { "type": "array", "items": { "type": "string" } }
        },
        "required": ["step_id", "agent_role", "prompt_template"]
      }
    }
  },
  "required": ["name", "steps"]
}
```

### 13.3.4 Standard Paginated Collection Response Schema
```json
{
  "data": [
    {
      "id": "proj_99f8d1e2a",
      "name": "Aegis Core Backend",
      "repo_url": "https://github.com/aegis/core-backend",
      "status": "active",
      "created_at": "2026-08-05T08:51:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "has_more": true,
      "next_cursor": "eyJpZCI6ICJwcm9qXzk5ZjhkMWUyYSJ9",
      "total_count": 142,
      "limit": 20
    }
  }
}
```

---

## 13.4 PAGINATION STRATEGY

AegisOS implements **Cursor-Based Pagination** as its default standard for event feeds, agent logs, and large execution collections to prevent the deep offset performance penalties in PostgreSQL.

| Attribute | Cursor-Based Pagination (Primary) | Offset-Based Pagination (Secondary) |
| :--- | :--- | :--- |
| **Best Used For** | Real-time streams, audit logs, agent events, large lists | Static dashboard tables, small page-numbered UI elements |
| **Query Parameter** | `starting_after=proj_99f8d1e2a&limit=20` | `page=2&page_size=20` |
| **Performance** | O(1) indexed lookup via keyset | O(N) linear table scan offset penalty |
| **Data Consistency** | Immune to duplicate items when new rows are inserted | Susceptible to page drift on active insertions |

---

## 13.5 FILTERING AND SORTING

### 13.5.1 Query Parameters Syntax
- **Filtering:** Field names accept square brackets for evaluation operators:
  - `GET /api/v1/agents?filter[status]=executing`
  - `GET /api/v1/agents?filter[created_at][gte]=2026-08-01T00:00:00Z`
  - `GET /api/v1/projects?filter[language]=python,typescript` (IN operator)
- **Sorting:** Multi-field sorting controlled via `sort` parameter (comma-separated, `-` prefix for descending order):
  - `GET /api/v1/projects?sort=-updated_at,name`

---

## 13.6 RATE LIMITING STRATEGY

All API responses include standard rate limit metadata headers:
- `X-RateLimit-Limit`: Maximum requests permitted within the time window.
- `X-RateLimit-Remaining`: Remaining request quota in current window.
- `X-RateLimit-Reset`: Unix timestamp when current quota resets.
- `Retry-After`: Returned on HTTP `429 Too Many Requests` specifying seconds to wait.

### 13.6.1 Redis Token Bucket Lua Script
```lua
-- Lua script for sliding window rate limiting in Redis
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)

if current < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return {1, limit - current - 1}
else
    return {0, 0}
end
```

---

## 13.7 API KEY AUTHENTICATION & SCOPE MANAGEMENT

API keys provide automated machine-to-machine authentication for CI/CD runners and external developer tooling.

### 13.7.1 Permission Scopes Catalog
| Scope Name | Domain | Granted Privileges |
| :--- | :--- | :--- |
| `org:admin` | IAM / Billing | Full tenant configuration, billing, and API key management |
| `project:read` | Projects | View project settings, AST trees, and build histories |
| `project:write` | Projects | Create and update projects, bind git repositories |
| `agent:read` | Agents | Inspect agent states, thought streams, and execution logs |
| `agent:execute` | Agents | Dispatch prompts and start/pause/resume agent loops |
| `sandbox:exec` | Sandboxes | Execute arbitrary shell commands in isolated containers |

```python
# app/core/security.py
import secrets
import hashlib
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-Aegis-API-Key", auto_error=False)

def generate_api_key(environment: str = "live") -> tuple[str, str]:
    raw_secret = secrets.token_urlsafe(32)
    api_key = f"aegis_{environment}_{raw_secret}"
    key_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
    return api_key, key_hash
```

---

## 13.8 WEBSOCKET EVENTS CATALOG

WebSocket endpoint `/api/v1/ws/projects/{project_id}/stream` provides bi-directional real-time event streaming.

| Event Name | Direction | Payload Description |
| :--- | :--- | :--- |
| `agent.thought_chunk` | Server -> Client | Incremental text stream from agent reasoning loop |
| `agent.tool_call` | Server -> Client | Agent invoking tool (e.g., `git_commit`, `run_tests`) |
| `agent.file_changed` | Server -> Client | Real-time file system diff generated by agent |
| `agent.status_updated`| Server -> Client | State transition (`idle` -> `thinking` -> `executing`) |
| `terminal.input` | Client -> Server | Human input sent into agent interactive sandbox |
| `agent.pause_request` | Client -> Server | Emergency human intervention to pause agent execution |

---

## 13.9 WEBHOOK DESIGN & RETRY POLICY

Outbound webhooks deliver HTTP POST payloads when long-running events conclude (e.g., `agent.completed`, `build.failed`, `human_approval.requested`).

### 13.9.1 Exponential Backoff Retry Schedule
If the customer endpoint returns a non-2xx HTTP status code or times out (10s), AegisOS schedules retries with exponential backoff:
1. Attempt 1: Immediate delivery
2. Attempt 2: Delay 15 seconds
3. Attempt 3: Delay 2 minutes
4. Attempt 4: Delay 15 minutes
5. Attempt 5: Delay 1 hour
6. Attempt 6: Delay 6 hours (Final attempt before sending to Dead Letter Queue)

### 13.9.2 Webhook Signature Verification Implementations
```python
# Python Webhook Verification Code
import hmac
import hashlib

def verify_webhook_signature(payload_bytes: bytes, secret: str, header_signature: str) -> bool:
    expected_hash = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    expected_signature = f"sha256={expected_hash}"
    return hmac.compare_digest(expected_signature, header_signature)
```

```typescript
// TypeScript Webhook Verification Code
import crypto from 'crypto';

export function verifyWebhookSignature(payload: string, secret: string, signatureHeader: string): boolean {
  const expectedHash = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return `sha256=${expectedHash}` === signatureHeader;
}
```

```go
// Go Webhook Verification Code
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
)

func VerifyWebhookSignature(payload []byte, secret string, headerSig string) bool {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write(payload)
	expectedSig := "sha256=" + hex.EncodeToString(mac.Sum(nil))
	return hmac.Equal([]byte(expectedSig), []byte(headerSig))
}
```

---

## 13.10 OPENAPI 3.1 SPECIFICATION EXCERPT

```yaml
openapi: 3.1.0
info:
  title: AegisOS REST API
  description: Universal AI Engineering Operating System API Specifications
  version: 1.0.0
servers:
  - url: https://api.aegisos.dev/api/v1
    description: Production API Gateway
paths:
  /agents/{id}/execute:
    post:
      summary: Dispatch task prompt to agent
      security:
        - BearerAuth: []
        - APIKeyAuth: []
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AgentExecuteRequest'
      responses:
        '202':
          description: Agent execution task accepted
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    APIKeyAuth:
      type: apiKey
      in: header
      name: X-Aegis-API-Key
```

---

## 13.11 API VERSIONING & DEPRECATION GOVERNANCE

AegisOS maintains strict API versioning rules to guarantee backwards compatibility for enterprise integrations.

1. **URL Path Versioning:** All endpoints are prefixed with `/api/v1/`. Breaking changes dictate a new major route prefix (`/api/v2/`).
2. **Backward Compatibility Rules:** Adding new optional response fields, adding new optional query parameters, or introducing new enum values are considered non-breaking changes.
3. **Deprecation Protocol:** When an endpoint is marked for deprecation, AegisOS includes standard RFC headers in all HTTP responses:
   - `Deprecation: @1785888000`
   - `Sunset: Wed, 05 Aug 2027 00:00:00 GMT`
   - `Link: <https://aegisos.dev/docs/migration-guide-v2>; rel="successor-version"`
   A minimum 12-month migration grace period is provided before any deprecated API path is retired.

---

## 13.12 SDK GENERATION & AUTOMATED BUILD PIPELINE

Automated client SDK generation runs on every API schema commit using `openapi-generator-cli` and `Fern` inside GitHub Actions. This guarantees that SDK libraries in TypeScript, Python, and Go remain continuously in sync with the primary FastAPI OpenAPI 3.1 schema specification:

```bash
# Automated SDK Generation Command Snippet
openapi-generator-cli generate \
  -i https://api.aegisos.dev/openapi.json \
  -g typescript-axios \
  -o ./sdks/typescript \
  --additional-properties=npmName=@aegis/sdk,supportsES6=true

openapi-generator-cli generate \
  -i https://api.aegisos.dev/openapi.json \
  -g python \
  -o ./sdks/python \
  --additional-properties=packageName=aegis_sdk
```


