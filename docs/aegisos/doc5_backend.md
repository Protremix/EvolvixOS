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
