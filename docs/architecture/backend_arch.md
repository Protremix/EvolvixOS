# 5. BACKEND ARCHITECTURE

## 5.1 SYSTEM ARCHITECTURAL OVERVIEW
The AegisOS backend is engineered using Python 3.11+ and the FastAPI asynchronous framework. It follows a layered, domain-driven micro-monolith architecture designed for horizontal scalability, high concurrency, and real-time streaming capability.

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

AegisOS maintains strict module boundaries following Clean Architecture and Domain-Driven Design (DDD) principles.

```
aegis_backend/
├── app/
│   ├── main.py                   # FastAPI Application Entrypoint & Lifespan Hooks
│   ├── core/                     # Platform Core & Cross-Cutting Infrastructure
│   │   ├── config.py             # BaseSettings Pydantic Configuration
│   │   ├── database.py           # Async SQLAlchemy Engine & Session Factory
│   │   ├── redis.py              # Async Redis Client Pool
│   │   ├── kafka.py              # Kafka Producer / Consumer Management
│   │   ├── security.py           # JWT Validation, Password Hashing, Encryption
│   │   ├── middleware.py         # Custom ASGI Middleware Pipeline
│   │   └── exceptions.py         # Centralized Exception Hierarchy
│   ├── api/                      # API Layer (Routers & Versioning)
│   │   ├── v1/
│   │   │   ├── router.py         # Top-Level V1 Aggregator Router
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py       # Authentication & IAM Endpoints
│   │   │   │   ├── projects.py   # Project Management & Repo Wiring
│   │   │   │   ├── agents.py     # Agent Execution & Stream Tracing
│   │   │   │   ├── workflows.py  # Multi-Agent Workflow Pipelines
│   │   │   │   ├── storage.py    # Artifact File Uploads/Downloads
│   │   │   │   └── health.py     # System Liveness & Readiness Probes
│   │   │   └── websockets/
│   │   │       └── terminal.py   # Real-Time Terminal & Telemetry WS
│   ├── services/                 # Domain Service Layer (Business Logic)
│   │   ├── agent_engine.py       # Autonomous Agent State Machine & ReAct Loop
│   │   ├── project_service.py    # Repository Context & AST Processing
│   │   ├── llm_router.py         # GPT-4o Prompt Assembly & Stream Dispatch
│   │   ├── sandbox_service.py    # Container Execution & Isolation Engine
│   │   └── workflow_engine.py   # DAG Task Execution & State Persistence
│   ├── models/                   # SQLAlchemy 2.0 ORM Database Models
│   │   ├── project.py
│   │   ├── agent.py
│   │   ├── workflow.py
│   │   └── user.py
│   ├── schemas/                  # Pydantic v2 Input/Output Validation Schemas
│   │   ├── project.py
│   │   ├── agent.py
│   │   └── telemetry.py
│   └── workers/                  # Asynchronous Background Execution (Celery)
│       ├── celery_app.py         # Celery Initialization & Configuration
│       └── tasks/
│           ├── code_analysis.py  # AST & Dependency Tree Parsing Tasks
│           ├── git_sync.py       # Async Git Fetch / Push Workers
│           └── agent_runner.py   # Long-Running Autonomous Agent Loop Tasks
├── tests/                        # Pytest Integration & Unit Test Suite
├── alembic/                      # Database Migration Scripts
├── Dockerfile                    # Production Container Definition
└── requirements.txt              # Strict Frozen Dependency Pinning
```

---

## 5.3 FASTAPI DEPENDENCY INJECTION PATTERN

AegisOS leverages FastAPI's idiomatic `Depends()` container to manage component lifetimes, database sessions, authentication states, and external client pools cleanly without global state leakage.

### 5.3.1 Asynchronous Database Session & Security Injection Implementation
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
    """Provides a transactional database session per request with auto-rollback on exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_redis() -> aioredis.Redis:
    """Provides an async Redis client instance from the connection pool."""
    return await get_redis_pool()

async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """Validates JWT access token and returns authenticated user entity."""
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

To ensure robust security, observability, and performance, requests pass through a strictly ordered chain of custom ASGI middlewares.

```
Incoming Request
      │
      ▼
┌─────────────────────────────────────────┐
│ 1. Security & CORS Headers Middleware   │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 2. Request ID & Correlation Middleware  │ (Injects X-Request-ID & sets structlog context)
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 3. OpenTelemetry / Prometheus Tracing   │ (Tracks active HTTP spans & latency histograms)
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 4. Sliding Window Rate Limit Middleware  │ (Evaluates Redis token bucket per IP/User)
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────┐
│ 5. DB Session Context Middleware        │
└─────────────────────────────────────────┘
      │
      ▼
   FastAPI Route Handler
```

### 5.4.1 Rate Limiting Middleware Code
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
        # Exclude health check endpoints
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

## 5.5 ERROR HANDLING STRATEGY & EXCEPTION HIERARCHY

AegisOS standardizes all API errors to comply with **RFC 7807 (Problem Details for HTTP APIs)**.

### 5.5.1 Custom Exception Hierarchy
```
AegisBaseException
├── AuthenticationError (401 Unauthorized)
├── PermissionDeniedError (403 Forbidden)
├── ResourceNotFoundError (404 Not Found)
├── ValidationError (422 Unprocessable Entity)
├── RateLimitExceededError (429 Too Many Requests)
└── DomainExecutionError (500 Internal Server Error)
    ├── AgentExecutionTimeout
    ├── LLMQuotaExceeded
    └── ContainerSandboxError
```

### 5.5.2 Centralized Exception Handler Implementation
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

## 5.6 BACKGROUND TASK PROCESSING (CELERY WORKERS)

Long-running operations—such as multi-file repository AST indexing, Docker sandbox execution, automated test execution, and non-streaming agent loops—are offloaded to distributed Celery worker processes backed by Redis / Kafka.

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

## 5.7 CONFIGURATION MANAGEMENT & SECRETS

Configuration management relies on Pydantic `BaseSettings` reading environment variables with strict validation.

```python
# app/core/config.py
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "AegisOS Backend"
    ENVIRONMENT: str = "production"
    API_V1_STR: str = "/api/v1"
    
    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Infrastructure Connections
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    
    REDIS_URL: str = "redis://localhost:6379/0"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    # LLM & AI Engine
    OPENAI_API_KEY: str
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    MAX_AGENT_LOOPS: int = 25
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

## 5.8 FILE UPLOAD & ARTIFACT PIPELINE

Source archives and build artifacts are processed using asynchronous chunk streaming directly to Amazon S3 / MinIO storage to avoid loading large payloads into API gateway memory.

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

## 5.9 WEBSOCKET & SSE STREAMING ARCHITECTURE

Real-time streaming is essential for delivering sub-second agent thinking logs, code terminal outputs, and LLM token streams.

### 5.9.1 Server-Sent Events (SSE) Endpoint for LLM Token Streaming
```python
# app/api/v1/endpoints/agents.py
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import json
import asyncio

router = APIRouter()

async def agent_token_stream_generator(agent_id: str) -> AsyncGenerator[str, None]:
    """Generates continuous token updates for an active agent thought stream."""
    for step in range(1, 10):
        await asyncio.sleep(0.1) # Simulating LLM token stream delay
        payload = {
            "agent_id": agent_id,
            "step": step,
            "delta": f" Analyzing AST module node #{step}...",
            "timestamp": "2026-08-05T08:51:00Z"
        }
        yield json.dumps(payload)

@router.get("/agents/{agent_id}/stream")
async def stream_agent_execution(agent_id: str):
    return EventSourceResponse(agent_token_stream_generator(agent_id))
```

---

## 5.10 HEALTH CHECK & OBSERVABILITY ENDPOINTS

The health check router exposes Kubernetes liveness, readiness, and startup probes that perform active network handshake validation across primary infrastructure dependencies.

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
    """Basic container process liveness check."""
    return {"status": "alive"}

@router.get("/readyz")
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Deep health probe validating database and cache connectivity."""
    health_status = {"status": "ok", "checks": {}}
    
    # Postgres check
    try:
        await db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Redis check
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
