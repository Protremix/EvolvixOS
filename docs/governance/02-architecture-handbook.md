# VERDIS GOVERNANCE DOCUMENT 02: ARCHITECTURE HANDBOOK

**Document ID:** VERDIS-GOV-02  
**Title:** Verdis Ecosystem Architectural Principles & System Design Patterns  
**Version:** 1.0.0  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT GOVERNANCE DOCUMENT  
**Applies To:** All System Architects, Software Engineers, Sub-Agents, and Infrastructure Engineers in the Verdis Ecosystem.

---

## TABLE OF CONTENTS
1. [Core Architectural Principles](#1-core-architectural-principles)
   1.1 [The Modular Monolith Paradigm](#11-the-modular-monolith-paradigm)
   1.2 [Prefer Upstream Technologies](#12-prefer-upstream-technologies)
   1.3 [Zero Duplication Rule (DRY)](#13-zero-duplication-rule-dry)
   1.4 [Security First & Architectural Supremacy](#14-security-first--architectural-supremacy)
2. [System Topography & Infrastructure Deployment](#2-system-topography--infrastructure-deployment)
   2.1 [Single Server Deployment Topology (`91.98.160.145`)](#21-single-server-deployment-topology-9198160145)
   2.2 [Docker Compose Orchestration Framework](#22-docker-compose-orchestration-framework)
   2.3 [Network Segmentation & Reverse Proxy Architecture](#23-network-segmentation--reverse-proxy-architecture)
   2.4 [Persistence, Storage & Backup Topography](#24-persistence-storage--backup-topography)
3. [Technology Stack Specification & Selection Rationale](#3-technology-stack-specification--selection-rationale)
   3.1 [Layer-1 Blockchain: Rust 1.80+ & Substrate 48](#31-layer-1-blockchain-rust-180--substrate-48)
   3.2 [AI Engineering Engine: Python 3.11 & FastAPI](#32-ai-engineering-engine-python-311--fastapi)
   3.3 [Frontend & Portals: React 18 & Vite 5](#33-frontend--portals-react-18--vite-5)
   3.4 [Persistence Layer: PostgreSQL 16 & Redis 7](#34-persistence-layer-postgresql-16--redis-7)
   3.5 [Technology Stack Summary Matrix](#35-technology-stack-summary-matrix)
4. [System Design Patterns](#4-system-design-patterns)
   4.1 [Substrate Pallet Architecture (Frame v2)](#41-substrate-pallet-architecture-frame-v2)
   4.2 [FastAPI Modular Router & Dependency Injection Pattern](#42-fastapi-modular-router--dependency-injection-pattern)
   4.3 [React Component Hierarchy & Zustand State Flow](#43-react-component-hierarchy--zustand-state-flow)
   4.4 [Clean Architecture & Hexagonal Layers](#44-clean-architecture--hexagonal-layers)
5. [Cross-System Integration Guidelines](#5-cross-system-integration-guidelines)
   5.1 [Substrate JSON-RPC / WebSocket Specifications](#51-substrate-json-rpc--websocket-specifications)
   5.2 [AegisOS REST API Specifications](#52-aegisos-rest-api-specifications)
   5.3 [Real-time Event Streaming via Server-Sent Events (SSE)](#53-real-time-event-streaming-via-server-sent-events-sse)
   5.4 [High-Throughput Inter-Service gRPC Mesh](#54-high-throughput-inter-service-grpc-mesh)
6. [The 7 Product Boundaries & Interface Contracts](#6-the-7-product-boundaries--interface-contracts)
   6.1 [Product 1: Verdis Chain](#61-product-1-verdis-chain)
   6.2 [Product 2: AegisOS (AI Engineering OS)](#62-product-2-aegisos-ai-engineering-os)
   6.3 [Product 3: Verdis Applications](#63-product-3-verdis-applications)
   6.4 [Product 4: Verdis Trust Layer](#64-product-4-verdis-trust-layer)
   6.5 [Product 5: Verdis Developer Cloud](#65-product-5-verdis-developer-cloud)
   6.6 [Product 6: Verdis Marketplace](#66-product-6-verdis-marketplace)
   6.7 [Product 7: Verdis Developer Platform](#67-product-7-verdis-developer-platform)
7. [Architecture Compliance & Review Checklists](#7-architecture-compliance--review-checklists)
   7.1 [Architectural Review Checklist](#71-architectural-review-checklist)
   7.2 [System Boundary Verification Checklist](#72-system-boundary-verification-checklist)

---

## 1. CORE ARCHITECTURAL PRINCIPLES

### 1.1 The Modular Monolith Paradigm
The Verdis Ecosystem adopts the **Modular Monolith** pattern across both its blockchain runtime and backend application layers. Instead of prematurely decomposing services into distributed microservices that introduce latency, network overhead, and complex partial failure modes, components are built as highly cohesive, loosely coupled internal modules.

- **In the Blockchain Runtime:** Modules are structured as Substrate Frame v2 Pallets. Each pallet manages its own isolated storage entries, dispatchable calls, events, and error types, while exposing clean public traits for cross-pallet interaction.
- **In the Backend Application (AegisOS):** Modules are structured as independent FastAPI APIRouters within a single codebase, utilizing dependency injection and clean domain interfaces.

```
 +-----------------------------------------------------------------------+
 |                    MODULAR MONOLITH ARCHITECTURE                      |
 +-----------------------------------------------------------------------+
 |  AEGISOS BACKEND (FastAPI Monolith)                                   |
 |  +---------------+ +---------------+ +---------------+ +------------+ |
 |  | Auth & Users  | | CTO Pipeline  | | DB Core Engine| | AI Engine  | |
 |  +---------------+ +---------------+ +---------------+ +------------+ |
 |         |                 |                 |               |         |
 |  =================== SHARED INTERNAL BUS / IN-MEMORY ================= |
 |                                                                       |
 |  VERDIS CHAIN RUNTIME (Substrate Monolith)                            |
 |  +---------------+ +---------------+ +---------------+ +------------+ |
 |  | Pallet VRDX   | | Pallet DPoS   | | Pallet Gov    | | WASM VM    | |
 |  +---------------+ +---------------+ +---------------+ +------------+ |
 +-----------------------------------------------------------------------+
```

### 1.2 Prefer Upstream Technologies
To minimize maintenance burden and guarantee long-term stability, Verdis strictly prefers well-maintained upstream open-source frameworks over custom re-implementations:
- **Consensus & State Machine:** Parity Substrate Frame v2 (Rust).
- **Backend API Engine:** FastAPI + Pydantic v2 + Async SQLAlchemy (Python).
- **UI & State Management:** React 18 + Vite 5 + Zustand + TailwindCSS (TypeScript).
- **Relational Storage:** PostgreSQL 16.
- **Caching & Event Queue:** Redis 7.
- **Container Orchestration:** Docker Compose.

### 1.3 Zero Duplication Rule (DRY)
Code or logic duplication across the Verdis Ecosystem is strictly forbidden. 
- Shared data types, constants, and validation rules between backend and frontend must be automatically synchronized using OpenAPI schemas or TypeScript generator scripts (`build_api_arch.py`).
- Shared cryptographic functions (e.g., SS58 address encoding, Blake2b hashing, Schnorrkel signatures) must utilize central ecosystem utility libraries (`blake2b_util.js`, `KeyManager.kt`, Substrate `sp-core`).

### 1.4 Security First & Architectural Supremacy
Architectural simplicity and defense-in-depth security take unconditional priority over feature velocity:
- No feature is merged without passing Step 3 (Architectural Review) and Step 7 (Security Audit) of the 9-Step CTO Pipeline.
- Performance optimizations must never compromise memory safety, state integrity, or boundary isolation.

---

## 2. SYSTEM TOPOGRAPHY & INFRASTRUCTURE DEPLOYMENT

### 2.1 Single Server Deployment Topology (`91.98.160.145`)
The Verdis production stack is consolidated on a dedicated, high-performance host node operating at IP address **`91.98.160.145`**.

```
 +-----------------------------------------------------------------------------+
 |              PRODUCTION HOST TOPOGRAPHY (IP: 91.98.160.145)                |
 +-----------------------------------------------------------------------------+
 |                                                                             |
 |  [ EXTERNAL INTERNET ]                                                      |
 |           |                                                                 |
 |           | Ports 80, 443 (HTTP/HTTPS) / Port 9944 (Substrate RPC)          |
 |           v                                                                 |
 |   +---------------------------------------------------------------------+   |
 |   | Host Network Ingress (UFW Firewall)                                 |   |
 |   +---------------------------------------------------------------------+   |
 |           |                                                                 |
 |           +-----------------------+-----------------------+                 |
 |           |                       |                       |                 |
 |           v                       v                       v                 |
 |   +---------------+       +---------------+       +---------------+         |
 |   | Nginx Reverse |       | Substrate Node|       | SSH Management|         |
 |   | Proxy Engine  |       | (Port 9944 WS)|       | (Port 22 SSH) |         |
 |   +---------------+       +---------------+       +---------------+         |
 |           |                                                                 |
 |           +-----------------------+                                         |
 |           |                       |                                         |
 |           v                       v                                         |
 |   +---------------+       +---------------+                                 |
 |   | AegisOS API   |       | React Frontend|                                 |
 |   | (Port 8000)   |       | Static Serve  |                                 |
 |   +---------------+       +---------------+                                 |
 |           |                                                                 |
 |           +-----------------------+                                         |
 |           |                       |                                         |
 |           v                       v                                         |
 |   +---------------+       +---------------+                                 |
 |   | PostgreSQL 16 |       | Redis 7 Cache |                                 |
 |   | (Port 5432)   |       | (Port 6379)   |                                 |
 |   +---------------+       +---------------+                                 |
 +-----------------------------------------------------------------------------+
```

### 2.2 Docker Compose Orchestration Framework
Infrastructure services are deployed using Docker Compose with host-network isolation. The primary orchestration file is `docker-compose-host-network.yml`:

```yaml
version: '3.8'

services:
  verdis-node:
    image: verdis/node:v1.0.0
    container_name: verdis-substrate-node
    network_mode: host
    restart: unless-stopped
    volumes:
      - /var/lib/verdis/chain-data:/data
    command:
      - "--chain=verdis-mainnet"
      - "--validator"
      - "--name=validator-01"
      - "--rpc-cors=all"
      - "--rpc-methods=safe"
      - "--rpc-port=9944"

  aegisos-api:
    image: verdis/aegisos:v1.0.0
    container_name: aegisos-backend
    network_mode: host
    restart: unless-stopped
    environment:
      - POSTGRES_SERVER=127.0.0.1
      - POSTGRES_PORT=5432
      - REDIS_URL=redis://127.0.0.1:6379/0
      - SUBSTRATE_RPC_URL=ws://127.0.0.1:9944
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16.2-alpine
    container_name: verdis-postgres
    network_mode: host
    restart: unless-stopped
    environment:
      POSTGRES_DB: verdis_aegisos
      POSTGRES_USER: verdis_admin
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    volumes:
      - /var/lib/verdis/postgres:/var/lib/postgresql/data
    secrets:
      - postgres_password

  redis:
    image: redis:7.2-alpine
    container_name: verdis-redis
    network_mode: host
    restart: unless-stopped
    command: redis-server --save 60 1 --loglevel notice
    volumes:
      - /var/lib/verdis/redis:/data

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
```

### 2.3 Network Segmentation & Reverse Proxy Architecture
Nginx terminates SSL/TLS and proxies inbound requests based on routing patterns:

```nginx
# /etc/nginx/sites-available/verdis.conf
server {
    listen 80;
    server_name verdis.network *.verdis.network;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name verdis.network;

    ssl_certificate /etc/letsencrypt/live/verdis.network/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/verdis.network/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    # Frontend Static Distribution
    location / {
        root /var/www/verdis-frontend;
        try_files $uri $uri/ /index.html;
    }

    # AegisOS REST API Proxy
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Real-time SSE Stream
    location /api/v1/events/stream {
        proxy_pass http://127.0.0.1:8000/api/v1/events/stream;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }

    # Substrate WebSocket RPC Proxy
    location /rpc {
        proxy_pass http://127.0.0.1:9944;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### 2.4 Persistence, Storage & Backup Topography
1. **Blockchain Storage:** Substrate RocksDB database stored at `/var/lib/verdis/chain-data`. Backed up via automated state snapshots.
2. **Relational Database:** PostgreSQL 16 stored at `/var/lib/verdis/postgres`. Automated daily `pg_dump` backups pushed to encrypted local storage.
3. **In-Memory Cache:** Redis 7 stored at `/var/lib/verdis/redis` with RDB persistence enabled (`save 60 1`).

---

## 3. TECHNOLOGY STACK SPECIFICATION & SELECTION RATIONALE

### 3.1 Layer-1 Blockchain: Rust 1.80+ & Substrate 48
- **Language:** Rust 1.80+ (Nightly toolchain for WASM target compilation).
- **Framework:** Substrate Frame v2 (sp-cli 48.0.0).
- **Consensus Architecture:**
  - **Block Production:** BABE (Blind Assignment for Blockchain Extension).
  - **Block Finality:** GRANDPA (GHOST-based Recursive Ancestor Deriving Prefix Agreement).
  - **Validator Set:** Delegated Proof-of-Stake (DPoS) with exactly **14 active validator slots**.
- **Tokenomics Specification:**
  - **Token Name:** VRDX
  - **Total Supply:** 100,000,000,000 VRDX (100 Billion VRDX fixed cap).
  - **Address Format:** SS58 Format with custom Network Prefix **`909`**.
  - **Decimals:** 18 decimals ($1 \text{ VRDX} = 10^{18} \text{ plancks}$).

### 3.2 AI Engineering Engine: Python 3.11 & FastAPI
- **Language:** Python 3.11.8+ (Strict type annotations mandatory).
- **Web Framework:** FastAPI 0.110.0+ (ASGI engine powered by Uvicorn).
- **Validation Engine:** Pydantic v2 (Strict schema validation).
- **ORM & Database:** SQLAlchemy 2.0 (Async Engine) + Alembic for migrations.
- **AI Model Integration:** GPT-4o API integration with structured function calling.

### 3.3 Frontend & Portals: React 18 & Vite 5
- **UI Core:** React 18.2+ with TypeScript strict mode.
- **Build Tooling:** Vite 5.1+ (Hot Module Replacement, lightning-fast bundling).
- **State Management:** Zustand (Global lightweight store) + TanStack Query v5 (Async server state).
- **Styling:** TailwindCSS 3.4+ (Design System consistency).

### 3.4 Persistence Layer: PostgreSQL 16 & Redis 7
- **Relational DB:** PostgreSQL 16.2 (JSONB support for AI memory structures, index optimization).
- **Cache & Message Bus:** Redis 7.2 (Pub/Sub for real-time events, task queues, rate limiting).

### 3.5 Technology Stack Summary Matrix

| Domain | Selected Technology | Version | Key Selection Criteria |
| :--- | :--- | :--- | :--- |
| **Blockchain Core** | Rust / Substrate | 1.80 / Substrate 48 | Memory safety, WASM runtime upgrades, DPoS support |
| **Consensus Engine** | BABE + GRANDPA | Native Substrate | Deterministic finality, sub-second block times |
| **Backend API** | Python / FastAPI | 3.11 / 0.110 | Asynchronous performance, native OpenAPI, Pydantic v2 |
| **Database** | PostgreSQL | 16.2 | ACID compliance, JSONB documents, enterprise reliability |
| **Cache / Queue** | Redis | 7.2 | Sub-millisecond latency, pub/sub stream capabilities |
| **Frontend UI** | React / Vite | 18.2 / 5.1 | Component reusability, fast build times, TypeScript support |
| **Containerization**| Docker Compose | 25.0 / v2.24 | Consistent deployment across development and production |

---

## 4. SYSTEM DESIGN PATTERNS

### 4.1 Substrate Pallet Architecture (Frame v2)
Substrate pallets in Verdis follow a standardized structural pattern:

```rust
// blockchain/pallets/vrdx-token/src/lib.rs
#![cfg_attr(not(feature = "std"), no_std)]

pub use pallet::*;

#[frame_support::pallet]
pub mod pallet {
    use frame_support::pallet_prelude::*;
    use frame_system::pallet_prelude::*;

    #[pallet::pallet]
    pub struct Pallet<T>(_);

    #[pallet::config]
    pub trait Config: frame_system::Config {
        type RuntimeEvent: From<Event<Self>> + IsType<<Self as frame_system::Config>::RuntimeEvent>;
        type CurrencyBalance: Parameter + Member + AtLeast32BitUnsigned + Default + Copy;
    }

    #[pallet::storage]
    #[pallet::getter(fn total_supply)]
    pub type TotalSupply<T: Config> = StorageValue<_, T::CurrencyBalance, ValueQuery>;

    #[pallet::storage]
    #[pallet::getter(fn balance_of)]
    pub type BalanceOf<T: Config> = StorageMap<
        _,
        Blake2_128Concat,
        T::AccountId,
        T::CurrencyBalance,
        ValueQuery,
    >;

    #[pallet::event]
    #[pallet::generate_deposit(pub(super) fn deposit_event)]
    pub enum Event<T: Config> {
        Transfer { from: T::AccountId, to: T::AccountId, amount: T::CurrencyBalance },
    }

    #[pallet::error]
    pub enum Error<T> {
        InsufficientBalance,
        Overflow,
    }

    #[pallet::call]
    impl<T: Config> Pallet<T> {
        #[pallet::call_index(0)]
        #[pallet::weight(10_000)]
        pub fn transfer(
            origin: OriginFor<T>,
            to: T::AccountId,
            amount: T::CurrencyBalance,
        ) -> DispatchResult {
            let sender = ensure_signed(origin)?;
            
            let sender_balance = BalanceOf::<T>::get(&sender);
            ensure!(sender_balance >= amount, Error::<T>::InsufficientBalance);

            BalanceOf::<T>::insert(&sender, sender_balance - amount);
            BalanceOf::<T>::mutate(&to, |balance| *balance += amount);

            Self::deposit_event(Event::Transfer { from: sender, to, amount });
            Ok(())
        }
    }
}
```

### 4.2 FastAPI Modular Router & Dependency Injection Pattern
FastAPI backend routes follow a strict modular router structure with async dependency injection:

```python
# aegisos/app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from aegisos.app.db.session import get_async_db
from aegisos.app.schemas.task import TaskCreate, TaskResponse
from aegisos.app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_engineering_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_async_db)
) -> TaskResponse:
    # Initiates a new autonomous engineering task and launches the 9-Step CTO Pipeline.
    service = TaskService(db)
    task = await service.create_task(task_in)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to initiate engineering task"
        )
    return task
```

### 4.3 React Component Hierarchy & Zustand State Flow
Frontend UI components are organized hierarchically, consuming atomic global stores powered by Zustand:

```typescript
// frontend/src/store/useTaskStore.ts
import { create } from 'zustand';

interface TaskState {
  activeTaskId: string | null;
  pipelineStep: number;
  isExecuting: boolean;
  setActiveTask: (id: string) => void;
  setPipelineStep: (step: number) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  activeTaskId: null,
  pipelineStep: 1,
  isExecuting: false,
  setActiveTask: (id) => set({ activeTaskId: id, isExecuting: true }),
  setPipelineStep: (step) => set({ pipelineStep: step }),
}));
```

### 4.4 Clean Architecture & Hexagonal Layers
Both backend and frontend follow Hexagonal Architecture (Ports and Adapters):
1. **Domain Layer:** Business models and core logic without external dependencies.
2. **Application Layer:** Use-case handlers and orchestration services (e.g., CTO Pipeline Engine).
3. **Infrastructure Layer:** Database drivers, HTTP clients, Redis adapters, and RPC wrappers.

---

## 5. CROSS-SYSTEM INTEGRATION GUIDELINES

### 5.1 Substrate JSON-RPC / WebSocket Specifications
External tools interact with Verdis Chain via JSON-RPC 2.0 over WebSocket (Port 9944):

- **Endpoint:** `ws://91.98.160.145:9944`
- **Standard Methods:**
  - `chain_getBlock`: Fetches block data by hash or number.
  - `state_getStorage`: Reads raw pallet storage keys.
  - `author_submitAndWatchExtrinsic`: Submits signed transactions and watches status stream.
- **Custom RPC Namespace:** `verdis_getValidatorSet`, `verdis_getDPoSMetrics`.

### 5.2 AegisOS REST API Specifications
- **Base URL:** `https://verdis.network/api/v1`
- **Format:** JSON payloads with standard envelope structures.
- **Error Format:**
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Engineering task task_98124 not found",
    "details": []
  }
}
```

### 5.3 Real-time Event Streaming via Server-Sent Events (SSE)
FastAPI provides low-latency streaming to React clients via SSE:

```python
# aegisos/app/api/v1/endpoints/events.py
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio

router = APIRouter()

@router.get("/events/stream")
async def stream_pipeline_events():
    async def event_generator():
        while True:
            # Yield SSE format event
            yield {
                "event": "step_transition",
                "data": '{"task_id": "t1", "step": 5, "status": "IN_PROGRESS"}'
            }
            await asyncio.sleep(2)

    return EventSourceResponse(event_generator())
```

### 5.4 High-Throughput Inter-Service gRPC Mesh
For internal microservice communication (e.g., AegisOS AI worker agents communicating with the Substrate indexer), gRPC over HTTP/2 is used:

```protobuf
// aegisos/proto/indexer.proto
syntax = "proto3";

package verdis.indexer;

service IndexerService {
  rpc GetLatestBlock (BlockRequest) returns (BlockResponse);
  rpc StreamChainEvents (EventFilter) returns (stream ChainEvent);
}

message BlockRequest {
  uint64 block_number = 1;
}

message BlockResponse {
  string block_hash = 1;
  uint64 block_number = 2;
  repeated string extrinsics = 3;
}

message EventFilter {
  string pallet_name = 1;
}

message ChainEvent {
  string pallet = 1;
  string event_name = 2;
  string data_json = 3;
}
```

---

## 6. THE 7 PRODUCT BOUNDARIES & INTERFACE CONTRACTS

```
 +-------------------------------------------------------------------------+
 |                      VERDIS 7-PRODUCT ECOSYSTEM                         |
 +-------------------------------------------------------------------------+
 | [P1: Verdis Chain] --------> Layer-1 DPoS Substrate Ledger              |
 | [P2: AegisOS]              --------> AI Engineering Operating System    |
 | [P3: Verdis Applications]  --------> Wallet, Explorer, Mobile, Portals    |
 | [P4: Verdis Trust Layer]   --------> Verdis ID & Release Signatures       |
 | [P5: Developer Cloud]      --------> Build Farm & Infrastructure        |
 | [P6: Marketplace]          --------> AI Agents & Contract Store         |
 | [P7: Developer Platform]   --------> SDKs, CLI & Universal APIs         |
 +-------------------------------------------------------------------------+
```

### 6.1 Product 1: Verdis Chain
- **Scope:** L1 Blockchain core runtime, BABE/GRANDPA consensus, 14 DPoS validators, VRDX token pallet, bridge logic, WASM smart contract execution environment.
- **Boundaries:** Exposes JSON-RPC/WebSocket endpoints (Port 9944). No direct REST endpoints.

### 6.2 Product 2: AegisOS (AI Engineering OS)
- **Scope:** Autonomous AI CTO engine, 9-Step CTO Pipeline, task scheduler, code generator, automated audit framework, PostgreSQL persistence.
- **Boundaries:** Exposes REST API (Port 8000) and SSE streams. Consumes Substrate RPC to record build audits on-chain.

### 6.3 Product 3: Verdis Applications
- **Scope:** User-facing frontend clients: Non-custodial Wallet, Block Explorer, Main Web Portal, Android/iOS mobile apps, Desktop binaries.
- **Boundaries:** Pure client-side applications consuming Verdis Chain RPC and AegisOS REST APIs. Zero server-side business logic.

### 6.4 Product 4: Verdis Trust Layer
- **Scope:** Cryptographic identity verification (Verdis ID), SS58 authorization, multi-sig release signing, immutable on-chain audit trails.
- **Boundaries:** Embedded inside Substrate Pallet Governance and consumed via AegisOS middleware.

### 6.5 Product 5: Verdis Developer Cloud
- **Scope:** Build farm, CI/CD automated test runners, validator node hosting, object storage, container registry.
- **Boundaries:** Orchestrated via Docker Compose and systemd on Host IP `91.98.160.145`.

### 6.6 Product 6: Verdis Marketplace
- **Scope:** Decentralized repository for publishing and purchasing AI agent sub-routines, WASM smart contract templates, and developer tools.
- **Boundaries:** Smart contract state stored on Verdis Chain; metadata hosted on AegisOS storage.

### 6.7 Product 7: Verdis Developer Platform
- **Scope:** Official SDKs (Rust, Python, TypeScript, Go), CLI (`verdis-cli`), API documentation, developer portal.
- **Boundaries:** Wraps REST, JSON-RPC, and gRPC endpoints into unified multi-language library distributions.

---

## 7. ARCHITECTURE COMPLIANCE & REVIEW CHECKLISTS

### 7.1 Architectural Review Checklist
When designing or modifying system modules, the architect or agent must verify:
- [ ] Module conforms to Modular Monolith principles (no premature microservices).
- [ ] Technology choice strictly aligns with standard stack (Rust, Python, React, PostgreSQL, Redis, Docker).
- [ ] No code or interface duplication introduced across frontend, backend, or chain layers.
- [ ] All external API endpoints expose OpenAPI 3.1 or JSON-RPC 2.0 compliant schemas.
- [ ] Memory safety and async non-blocking execution guaranteed across all I/O paths.

### 7.2 System Boundary Verification Checklist
- [ ] Blockchain logic resides exclusively within Substrate pallets (`blockchain/pallets/`).
- [ ] Backend API endpoints reside strictly within FastAPI routers (`aegisos/app/api/v1/`).
- [ ] User Interface components contain zero raw business logic and consume state via Zustand/TanStack Query.
- [ ] Target host port bindings strictly adhere to deployment topology (`22`, `80`, `443`, `8000`, `9944`).

---
*End of Governance Document 02 — Verdis Ecosystem Architectural Principles & System Design Patterns.*
