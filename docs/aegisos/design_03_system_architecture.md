# AegisOS System Architecture Specification
**Document Version:** 1.0.0  
**Target Platform:** Single-Node to Enterprise Multi-Cluster  
**Target Systems:** Web, Mobile, Blockchain, Machine Learning, Microservices  

---

## 3. SYSTEM ARCHITECTURE

AegisOS is an enterprise-grade, universal AI Engineering Operating System designed to autonomously plan, execute, verify, and maintain complex software projects across heterogeneous technology stacks. Whether managing a React/Node.js web application, a Flutter mobile app, a Solidity/Anchor smart contract suite, a PyTorch machine learning pipeline, or a high-throughput Go microservice cluster, AegisOS provides unified orchestration, sandboxed runtime execution, multi-tiered memory systems, and granular human-in-the-loop oversight.

The system is architected to operate efficiently on a **single high-performance server** (e.g., 64-vCPU, 256GB RAM bare-metal instance or VM) for startup and single-tenant deployments, while maintaining complete horizontal scaling capabilities to expand seamlessly across Kubernetes multi-region clusters for global enterprise workloads.

```
+---------------------------------------------------------------------------------------------------+
|                                     AEGISOS HIGH-LEVEL TOPOLOGY                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  |                                  FRONTEND LAYER (Next.js 15)                                |  |
|  |  +-----------------------+  +--------------------------+  +------------------------------+  |  |
|  |  | Interactive DAG Canvas|  | Real-Time Streaming Logs |  | Human Approval Gate Manager  |  |  |
|  |  +-----------------------+  +--------------------------+  +------------------------------+  |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 | HTTPS / SSE / WebSockets                        |
|  +----------------------------------------------v----------------------------------------------+  |
|  |                                     API GATEWAY (Traefik v3)                                |  |
|  |  [ Rate Limiting | TLS Termination | JWT & API Key Validation | Route Distribution ]        |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 | gRPC / Internal REST                            |
|  +----------------------------------------------v----------------------------------------------+  |
|  |                                BACKEND CORE & ORCHESTRATOR (FastAPI)                        |  |
|  |  +-------------------------+  +-------------------------+  +-----------------------------+  |  |
|  |  |  Meta-Orchestrator      |  |  Agent FSM Lifecycle    |  |  Capability & Policy Engine |  |  |
|  |  +-------------------------+  +-------------------------+  +-----------------------------+  |  |
|  +----+-----------------------------------------+-----------------------------------------+----+  |
|       |                                         |                                         |       |
|       | Temporal Signals / Events               | Task Dispatch                           | Events|
|  +----v--------------------+               +----v--------------------+               +----v----+  |
|  | TEMPORAL WORKFLOW ENGINE|               |  NATS JETSTREAM BUS     |               | REDIS 7 |  |
|  | (Durable Execution)     |               |  (Event-Driven Bus)     |               | (Cache) |  |
|  +----+--------------------+               +----+--------------------+               +----+----+  |
|       |                                         |                                         |       |
|       +-----------------------------------------+-----------------------------------------+       |
|                                                 | Task Payload / Context                          |
|  +----------------------------------------------v----------------------------------------------+  |
|  |                              AGENT RUNTIME ENVIRONMENT (AEN)                                |  |
|  |  +---------------------------------------------------------------------------------------+  |  |
|  |  |                             SECURITY SANDBOX CONTAINMENT                              |  |  |
|  |  |   +-----------------------+   +-----------------------+   +-----------------------+   |  |  |
|  |  |   | Tier 1: Linux Cgroups |   | Tier 2: gVisor runsc  |   | Tier 3: AWS Firecracker|  |  |  |
|  |  |   +-----------------------+   +-----------------------+   +-----------------------+   |  |  |
|  |  +---------------------------------------------------------------------------------------+  |  |
|  |  +-----------------------+   +-----------------------+   +-------------------------------+  |  |
|  |  | Tool Execution Layer  |   | LLM Provider Gateway  |   | Token & Cost Rate Limiter     |  |  |
|  |  +-----------------------+   +-----------------------+   +-------------------------------+  |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 | Reads / Writes / Embeddings                     |
|  +----------------------------------------------v----------------------------------------------+  |
|  |                                   PERSISTENCE & MEMORY LAYER                                |  |
|  |  +------------------------------------+  +-----------------------------------------------+  |  |
|  |  | Primary Database: PostgreSQL 16    |  | Vector Engine: pgvector / Qdrant              |  |  |
|  |  | (Relational, JSONB, Audit Logs)    |  | (Short, Long, Project & Global Memory)        |  |  |
|  |  +------------------------------------+  +-----------------------------------------------+  |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

### Backend Architecture

The backend layer serves as the control plane for AegisOS, responsible for API handling, agent lifecycle management, security token validation, external service integrations, and task dispatching.

#### Language and Framework Selection & Justification

AegisOS selects **Python 3.12+ with FastAPI** as its primary core backend framework, augmented by high-performance **Rust micro-modules** (bound via `PyO3`) for latency-critical tasks such as Abstract Syntax Tree (AST) parsing, token calculation, and vector metric computations.

| Metric / Criteria | Python + FastAPI | Node.js + Express / NestJS | Go (Golang) | Chosen Stack Justification |
| :--- | :--- | :--- | :--- | :--- |
| **AI/ML Ecosystem Integration** | **Native** (LangChain, LlamaIndex, PyTorch, HuggingFace, OpenAI, Anthropic SDKs) | Secondary (Wrapper wrappers, missing native scientific tools) | Minimal (Requires manual CGO wrappers or HTTP REST interfaces) | Python is the undeniable lingua franca of the AI ecosystem. Direct integration with model libraries without IPC overhead is critical. |
| **Async I/O Performance** | High (`uvloop` + `asyncio`, ~50k req/sec) | High (`uvlib` event loop, ~60k req/sec) | Very High (Goroutines, ~120k req/sec) | FastAPI running on `uvloop` (C-based event loop) delivers near-Go I/O throughput while retaining full Python ecosystem capabilities. |
| **Data Validation & Serialization** | Excellent (Pydantic v2 written in Rust) | Good (Zod, class-validator) | Manual / Code Generation | Pydantic v2 compiles schema parsing into native C/Rust, eliminating JSON serialization bottlenecks in AI tool invocations. |
| **Type Safety & Maintainability** | High (Strict MyPy / Pyright static typing) | High (TypeScript) | High (Static typing) | Python 3.12 strict typing paired with Pydantic ensures absolute type enforcement across agent tool interfaces. |

#### Architectural Design Patterns

The backend strictly implements **Clean Architecture (Hexagonal / Ports and Adapters)** integrated with **Command Query Responsibility Segregation (CQRS)**:

1. **Domain Layer (Core Business Rules):** Contains pure entities (`Task`, `Agent`, `Workflow`, `MemoryItem`, `CostLedger`) completely independent of frameworks, databases, or third-party APIs.
2. **Application Use Cases (Ports):** Defines explicit interfaces (Ports) for task execution, agent coordination, tool dispatching, and memory retrieval.
3. **Adapters Layer:** Implements concrete drivers (Adapters) for PostgreSQL, Temporal, Redis, NATS, GitHub API, Docker/gVisor runtime, and LLM provider endpoints.
4. **CQRS Separation:**
   - **Command Pipeline:** Write operations (e.g., initiating task, updating agent state, committing tool result) pass through strict transactional workflows via Temporal and PostgreSQL.
   - **Query Pipeline:** Read operations (e.g., rendering real-time dashboard state, querying execution history, retrieving vector search results) bypass heavy workflow state machines and query indexed read-replicas or Redis directly.

```
       +-------------------------------------------------------------------+
       |                        HEXAGONAL ARCHITECTURE                     |
       +-------------------------------------------------------------------+
       |                                                                   |
       |     +-------------------------------------------------------+     |
       |     |                    PRIMARY ADAPTERS                   |     |
       |     |  [ REST API ]   [ gRPC Server ]   [ Webhook Handler ] |     |
       |     +---------------------------+---------------------------+     |
       |                                 |                                 |
       |                                 v                                 |
       |     +-------------------------------------------------------+     |
       |     |                     INPUT PORTS                       |     |
       |     |   [ TaskServicePort ]      [ AgentOrchestratorPort ]  |     |
       |     +---------------------------+---------------------------+     |
       |                                 |                                 |
       |                                 v                                 |
       |     +-------------------------------------------------------+     |
       |     |                    DOMAIN CORE                        |     |
       |     |   Entities: Agent, Task, Memory, Project, CostLedger  |     |
       |     |   Value Objects: TaskStatus, Capability, TokenBudget |     |
       |     +---------------------------+---------------------------+     |
       |                                 |                                 |
       |                                 v                                 |
       |     +-------------------------------------------------------+     |
       |     |                    OUTPUT PORTS                       |     |
       |     |   [ PersistencePort ]      [ ExecutionSandboxPort ]   |     |
       |     |   [ VectorStorePort ]      [ LLMProviderPort ]        |     |
       |     +---------------------------+---------------------------+     |
       |                                 |                                 |
       |                                 v                                 |
       |     +-------------------------------------------------------+     |
       |     |                    SECONDARY ADAPTERS                 |     |
       |     |  [ PostgresAdapter ]  [ gVisorAdapter ]  [ OpenAI ]   |     |
       |     +-------------------------------------------------------+     |
       |                                                                   |
       +-------------------------------------------------------------------+
```

#### API Style Strategy

AegisOS utilizes a **Hybrid Multi-Protocol API Strategy** tailored to specific system communication boundaries:

* **RESTful HTTP/3 API (OpenAPI v3.1):** Exposed for external administrative operations, UI dashboard CRUD tasks, project creation, user management, and third-party Webhook ingestion (GitHub, GitLab, Jira, CircleCI).
* **gRPC (Protobuf v3):** Deployed for high-frequency internal microservice-to-microservice communication, specifically between the core Orchestrator backend and isolated Agent Execution Nodes (AEN). gRPC minimizes serialization latency and supports multiplexed binary streams.
* **Server-Sent Events (SSE):** Utilized for unidirectionally streaming real-time LLM token output, terminal execution stdout/stderr logs, and task step progress updates directly from the backend to the frontend UI.
* **WebSockets (Socket.io protocol):** Deployed for bidirectional collaborative interactive terminal emulation (xterm.js integration) and multi-user active cursor and canvas state synchronization.

#### Background Job Processing Architecture

Background execution is structured into two distinct execution domains:

1. **Short-Lived Ephemeral Operations (Celery + Redis):** Fast, stateless tasks such as sending webhook notifications, calculating code metrics, compressing log archives, and generating static vector embeddings.
2. **Durable Multi-Step Workflow Execution (Temporal.io):** Complex, long-running agent execution workflows that span minutes, hours, or days. Temporal guarantees state persistence across server reboots, network partitions, and process crashes without losing context or requiring agent task restart from scratch.

---

### Frontend Architecture

The AegisOS frontend provides an enterprise-grade command center for developers, team leads, and system administrators to manage, monitor, and interact with autonomous AI agents.

#### Framework Selection & Justification

AegisOS standardizes on **Next.js 15 (React 19 App Router)** with **TypeScript**.

* **React 19 & Next.js App Router:** Offers Server Components (RSC) for zero-bundle-size initial page renders, native Streaming SSR for real-time AI dashboards, and seamless integration with the industry-standard Vercel AI SDK (`useChat`, `useCompletion`).
* **Tailwind CSS + Shadcn UI + Radix UI:** Provides an accessible, highly customizable design system adhering to strict WCAG 2.1 AA accessibility standards.
* **React Flow / React Flow Pro:** Serves as the interactive visualization engine for rendering dynamic multi-agent execution Directed Acyclic Graphs (DAGs), enabling users to inspect sub-task dependencies, execution status, and agent memory state in real time.

#### State Management Architecture

A hybrid, multi-tier state management paradigm is enforced to separate persistent domain state, transient UI state, and reactive graph state:

```
+-----------------------------------------------------------------------------------+
|                            FRONTEND STATE ARCHITECTURE                            |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  +----------------------------------+   +--------------------------------------+  |
|  |       SERVER STATE LAYER         |   |         CLIENT UI STATE LAYER        |  |
|  |     (TanStack Query v5)          |   |              (Zustand)               |  |
|  | - API Query Caching              |   | - Active Workspace Tabs              |  |
|  | - Optimistic Mutations           |   | - Modal Visibility / Drawers         |  |
|  | - Background Revalidation        |   | - User Preference Configurations     |  |
|  +----------------------------------+   +--------------------------------------+  |
|                                                                                   |
|  +----------------------------------+   +--------------------------------------+  |
|  |    ATOMIC GRAPH CANVAS STATE     |   |      REAL-TIME STREAMING STATE       |  |
|  |             (Jotai)              |   |       (Vercel AI SDK + SSE)          |  |
|  | - Node / Edge Graph Coordinates  |   | - Streaming Token Buffers            |  |
|  | - Selection Highlighting         |   | - Active Terminal Output Stream      |  |
|  | - Zoom & Pan Viewport State      |   | - Agent Live Telemetry Feeds         |  |
|  +----------------------------------+   +--------------------------------------+  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

#### Real-Time Update Pipeline

To support real-time token streaming and responsive agent interaction without browser lag, the frontend employs a multiplexed SSE stream listener coupled with custom web worker decoders:

* **Token Streaming:** Raw SSE chunks from `/api/v1/agent/stream` are processed in a dedicated Web Worker to prevent UI main-thread blocking during high-volume token generation (up to 200 tokens/sec).
* **Terminal Emulation:** xterm.js instances attach directly to WebSocket streaming channels (`/ws/terminal/{execution_id}`), enabling interactive human intervention when an agent prompts for terminal user input.

---

### AI Orchestrator

The AI Orchestrator is the central brain of AegisOS, responsible for decomposing macro software engineering goals into structured, executable execution plans, assigning agents, monitoring execution, and ensuring deterministic task completion.

#### Coordination Topology: Hierarchical Meta-Orchestrator

AegisOS employs a **Hierarchical Meta-Orchestrator Architecture** with dynamic peer-to-peer negotiation fallbacks:

```
                             +-----------------------+
                             |  CHIEF ARCHITECT AGENT |
                             |   (Meta-Orchestrator)  |
                             +-----------+-----------+
                                         |
            +----------------------------+----------------------------+
            |                            |                            |
            v                            v                            v
+-----------------------+    +-----------------------+    +-----------------------+
|  FRONTEND SPECIALIST  |    |  BACKEND SPECIALIST   |    |  SMART CONTRACT AGENT |
|   (React/Next.js UI)  |    |  (FastAPI/Postgres)   |    |  (Solidity/Anchor)    |
+-----------+-----------+    +-----------+-----------+    +-----------+-----------+
            |                            |                            |
            +----------------------------+----------------------------+
                                         | Dynamic Code Review / P2P Validation
                                         v
                             +-----------------------+
                             |    QA & SECURITY AGENT|
                             |  (Testing & Auditing) |
                             +-----------------------+
```

1. **Chief Architect Agent (Level 0 - Meta-Orchestrator):**
   - Receives raw project tickets (e.g., "Implement ERC-20 staking contract with React dashboard and FastAPI analytics endpoint").
   - Analyzes project repository context, global memory, and framework guidelines.
   - Generates a formal **Task DAG (Directed Acyclic Graph)** specifying strict sub-task dependencies, inputs, outputs, and validation criteria.
2. **Domain Specialist Agents (Level 1 - Execution Sub-Graph):**
   - Autonomous, domain-trained agents specialized in targeted technology stacks (Frontend, Backend, Mobile, Blockchain, ML, DevOps).
   - Operates strictly within assigned DAG node boundaries.
3. **Peer-to-Peer Agent Negotiation Protocols:**
   - When inter-agent code dependencies clash (e.g., Backend Agent alters an API response schema required by the Frontend Agent), agents initiate a direct P2P negotiation protocol over NATS JetStream to reconcile interface contracts before requesting human review.

#### Agent Lifecycle Management

Agent state transitions are governed by an explicit Finite State Machine (FSM):

```
+---------------------------------------------------------------------------------------------------+
|                                   AGENT LIFECYCLE STATE MACHINE                                   |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  +--------------+    Initialization   +--------------+    Task Assigned    +--------------+       |
|  |  PROVISIONED |  -----------------> | INITIALIZING |  -----------------> |     IDLE     |       |
|  +--------------+                     +--------------+                     +-------+------+       |
|                                                                                    |              |
|                                                                                    | Plan Ready   |
|                                                                                    v              |
|  +--------------+     Error / Trap    +--------------+    Execution Start  +--------------+       |
|  |    FAILED    |  <----------------- |  EXECUTING   |  <----------------- |   PLANNING   |       |
|  +--------------+                     +-------+------+                     +--------------+       |
|         ^                                     |                                                   |
|         | Max Retries                         | Approval Required                                 |
|         | Exceeded                            v                                                   |
|  +--------------+   Human Approved    +--------------------------+                                |
|  |  RETRYING    |  <----------------- | WAITING_HUMAN_APPROVAL   |                                |
|  +--------------+                     +--------------------------+                                |
|         ^                                     |                                                   |
|         | Failed Checks                       | Passed Checks                                     |
|         |                                     v                                                   |
|  +--------------+     Task Complete   +--------------+                                            |
|  |   COMPLETED  |  <----------------- |  VERIFYING   |                                            |
|  +--------------+                     +--------------+                                            |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Agent Health Monitoring & Loop Detection

To guarantee system stability and prevent infinite execution or hallucination loops, the Orchestrator runs continuous watchdog telemetry:

* **Heartbeat Verification:** Every agent instance emits a cryptographic heartbeat signal every 5 seconds. If missed for 3 consecutive intervals (15 seconds), the agent state is transitioned to `UNHEALTHY` and auto-healed.
* **Hallucination & Infinite Loop Trap Detector:** The watchdog analyzes the sequence of tool invocations. If an agent executes identical tool commands with identical parameters three consecutive times without advancing task state, or generates repetitive error responses, the circuit breaker opens, suspending the agent and escalating to human approval (`WAITING_HUMAN_APPROVAL`).
* **Resource Sanity Constraints:** Real-time RAM, CPU, and disk usage monitoring terminates agents exceeding 90% allocated sandbox limits.

#### Agent Scaling & Load Management

Agents scale dynamically based on task backlog depth and LLM token budget capacity:

* **Single-Server Mode:** Worker pool dynamically scales green threads / processes up to CPU core count ($N_{workers} = 	ext{CPU\_Cores} 	imes 2$).
* **Multi-Server Enterprise Mode:** Temporal workers scale horizontally across Kubernetes worker nodes using Horizontal Pod Autoscalers (HPA) triggered by custom NATS JetStream queue lag metrics.

---

### Agent Runtime

The Agent Runtime Environment (AEN) provides secure, isolated, and deterministic sandboxes where individual AI agents execute tool commands, write code, run terminal commands, compile binaries, and execute unit tests.

#### Execution Model & Sandbox Containment Architecture

To support **ANY** project type securely—from standard Web apps to raw untrusted kernel drivers, Solana smart contracts, or C++ binaries—AegisOS deploys a **3-Tiered Security Isolation Framework**:

```
+---------------------------------------------------------------------------------------------------+
|                                 3-TIER SANDBOX CONTAINMENT ARCHITECTURE                            |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | TIER 1: LIGHTWEIGHT PROCESS CONTAINMENT (cgroups v2 + Linux Namespaces)                       |  |
|  | - Used for: Non-executable tasks, documentation generation, static code analysis, linting.   |  |
|  | - Isolation: PID, mount, net, IPC, UTS namespaces + restricted seccomp BPF filters.          |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | TIER 2: USERSPEACE KERNEL SANDBOX (gVisor runsc Container Isolation)                          |  |
|  | - Used for: Standard web app builds, Node.js/Python tests, API server execution.             |  |
|  | - Isolation: Sentry ring-buffer syscall interception in userspace. Virtualized network stack. |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | TIER 3: EPHEMERAL MICROVM CONTAINMENT (AWS Firecracker MicroVMs)                              |  |
|  | - Used for: Untrusted binary compilation, Docker-in-Docker, Blockchain node execution, ML.   |  |
|  | - Isolation: KVM hypervisor isolation. Cold boot time < 50ms. Dedicated kernel instance.     |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Tool Access & Permissions Engine

Agent capabilities are restricted via explicit **Model Context Protocol (MCP)** tool manifests enforcing strict Least Privilege access controls:

```json
{
  "$schema": "https://aegisos.dev/schemas/tool-manifest.v1.json",
  "tool_id": "git_commit_and_push",
  "display_name": "Git Commit & Remote Push",
  "permission_tier": "PRIVILEGED_ACTION",
  "require_human_approval": true,
  "allowed_roles": ["ProjectMaintainer", "LeadAgent"],
  "rate_limit": {
    "max_calls_per_minute": 5
  },
  "parameters": {
    "type": "object",
    "properties": {
      "repository_id": { "type": "string", "format": "uuid" },
      "branch_name": { "type": "string", "pattern": "^[a-zA-Z0-9_-]+$" },
      "commit_message": { "type": "string", "maxLength": 500 }
    },
    "required": ["repository_id", "branch_name", "commit_message"]
  }
}
```

* **Human-In-The-Loop (HITL) Gateways:** Any tool categorized as `PRIVILEGED_ACTION` (e.g., pushing code to remote `main` branch, running cloud infrastructure deletion commands, executing smart contract deployments) triggers an automatic suspension, posting an approval request card to the UI and Slack/Discord webhooks.

#### Rate Limiting & Budget Management

Every agent run is bound by strict monetary and rate-limiting constraints:

* **Token Bucket Algorithm:** Enforces requests-per-minute (RPM) and tokens-per-minute (TPM) limits across model providers (OpenAI, Anthropic, Google, local Ollama/vLLM endpoints).
* **Cost Allocation Ledger:** Real-time tracking middleware calculates cumulative task cost based on prompt/completion token pricing.
* **Hard & Soft Stop Budget Controls:**
  - **Soft Limit (80% Budget):** Triggers a system alert and instructs agent to optimize prompt context window.
  - **Hard Limit (100% Budget):** Immediately halts agent execution, saves context state to long-term memory, and marks task as `SUSPENDED_BUDGET_EXCEEDED`.

---

### Task Queue & Scheduling

AegisOS handles asynchronous task execution, background scheduling, and long-running multi-agent workflows using a robust, fault-tolerant orchestration architecture.

#### Technology Choice & Comparison

AegisOS standardizes on **Temporal.io** as its primary workflow engine, backed by **Redis 7.2** for high-velocity volatile queuing.

| Architecture Option | Temporal.io | Celery + Redis | BullMQ + Node.js | Chosen Approach & Justification |
| :--- | :--- | :--- | :--- | :--- |
| **State Persistence Model** | Event-Sourced (Full history replay) | Ephemeral (Lost on worker crash) | Ephemeral / Redis-bound | **Temporal.io chosen.** AI Agent workflows are stateful and long-running. Event sourcing guarantees that if a server reboots mid-task, Temporal replays state to the exact step without re-executing LLM prompts. |
| **Long-Running Durability** | Infinite (Hours to months) | Poor (Timeouts, worker locks break) | Moderate (Job stall limiters) | Temporal allows agents to await human approval for days without holding memory or thread locks. |
| **Deterministic Replay** | Native support | None | None | Essential for debugging agent execution failures step-by-step. |

#### Task State Machine & Transitions

```
+---------------------------------------------------------------------------------------------------+
|                                     TASK STATE TRANSITION MATRIX                                  |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ CREATED ] ---> [ ENQUEUED ] ---> [ SCHEDULED ] ---> [ RUNNING ] ---> [ SUCCESS ]               |
|                                                            |                                      |
|                                                            +---> [ WAITING_HUMAN_INPUT ]          |
|                                                            |            |                         |
|                                                            |            v                         |
|                                                            +---> [ RETRYING ]                     |
|                                                            |            |                         |
|                                                            |            v                         |
|                                                            +---> [ FAILED ] ---> [ DEAD_LETTER ]  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Priority Queue Architecture

Tasks are routed into 4 priority queues managed via Weighted Fair Queuing (WFQ):

1. **P0: Emergency Hotfix Queue (Weight: 50%):** Production patch deployment, critical security vulnerability resolution.
2. **P1: Interactive User Request Queue (Weight: 30%):** Direct user-initiated chat commands and UI DAG triggers.
3. **P2: CI/CD Pipeline Automation Queue (Weight: 15%):** Automated pull request reviews, test suite generation.
4. **P3: Background Maintenance Queue (Weight: 5%):** Static code analysis, documentation updates, vector index optimizations.

#### Retry Policies and Dead-Letter Queue (DLQ) Management

* **Exponential Backoff with Jitter:**
  $$	ext{Backoff Interval} = \min\left(T_{	ext{max}}, T_{	ext{base}} 	imes 2^{	ext{attempt}}ight) \pm 	ext{RandomJitter}$$
  Where $T_{	ext{base}} = 2	ext{s}$ and $T_{	ext{max}} = 300	ext{s}$.
* **Error Classification Engine:**
  - *Transient Errors* (API 503, network timeout, rate limit 429): Retried up to 5 times.
  - *Non-Retryable Errors* (Invalid tool parameter schema, authorization failure, model context limit exceeded): Instantly routed to Dead-Letter Queue (DLQ).
* **DLQ Management:** Poison-pill isolation preserves full task context in the database and dispatches a high-priority event to the Orchestrator for diagnosis.

---

### Databases & Relational Schema Design

AegisOS employs a single primary relational database paired with distributed caching and vector storage engines.

#### Primary Database Selection: PostgreSQL 16

For single-server deployments, **PostgreSQL 16** is the optimal choice. It offers unmatched ACID reliability, mature JSONB indexing, Row-Level Security (RLS) multi-tenancy, and native vector embedding search via the `pgvector` extension. This enables zero-dependency startup on a single server, with zero code changes required when scaling horizontally to managed clusters (e.g., AWS Aurora PostgreSQL or Citus).

* **Cache Layer:** **Redis 7.2** (Used for transient session state, distributed locks via Redlock, and prompt template caching).
* **Vector Engine:** Native **`pgvector`** embedded within PostgreSQL 16 for single-server mode; abstractable to **Qdrant** cluster for enterprise multi-node mode.

#### Full Database Schema Design (16 Production Tables)

Below is the complete SQL Schema definition comprising 16 production tables, full column definitions, foreign keys, constraints, and explicit performance indexes:

```sql
-- PostgreSQL 16 Production Schema for AegisOS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. TENANTS TABLE
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'community',
    max_concurrent_agents INT NOT NULL DEFAULT 5,
    monthly_budget_limit NUMERIC(10, 2) NOT NULL DEFAULT 100.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tenants_slug ON tenants(slug);

-- 2. USERS TABLE
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'developer',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_tenant_role ON users(tenant_id, role);

-- 3. PROJECTS TABLE
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    project_type VARCHAR(50) NOT NULL, -- web, mobile, blockchain, ml, microservice
    description TEXT,
    repository_url VARCHAR(512),
    default_branch VARCHAR(100) NOT NULL DEFAULT 'main',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_projects_type ON projects(project_type);

-- 4. PROJECT REPOSITORIES TABLE
CREATE TABLE project_repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- github, gitlab, bitbucket
    repo_owner VARCHAR(255) NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    webhook_secret_encrypted TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_repo_project_provider ON project_repositories(project_id, provider, repo_owner, repo_name);

-- 5. AGENTS TABLE
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    role_type VARCHAR(100) NOT NULL, -- chief_architect, frontend, smart_contract, etc.
    model_provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    model_name VARCHAR(100) NOT NULL DEFAULT 'gpt-4o',
    system_prompt TEXT NOT NULL,
    temperature NUMERIC(3,2) NOT NULL DEFAULT 0.20,
    is_template BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_agents_tenant_role ON agents(tenant_id, role_type);

-- 6. AGENT CAPABILITIES TABLE
CREATE TABLE agent_capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_name VARCHAR(100) NOT NULL,
    permission_level VARCHAR(50) NOT NULL DEFAULT 'READ_ONLY',
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_agent_capability ON agent_capabilities(agent_id, capability_name);

-- 7. TASKS TABLE
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'created', -- created, enqueued, running, completed, failed
    priority VARCHAR(20) NOT NULL DEFAULT 'P2', -- P0, P1, P2, P3
    assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    cost_accumulated NUMERIC(10, 4) DEFAULT 0.0000,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- 8. TASK STEPS TABLE
CREATE TABLE task_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_number INT NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_payload JSONB DEFAULT '{}'::jsonb,
    output_payload JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
CREATE INDEX idx_task_steps_task ON task_steps(task_id, step_number);

-- 9. AGENT RUNS TABLE
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    sandbox_id VARCHAR(255),
    execution_tier VARCHAR(50) NOT NULL DEFAULT 'tier2_gvisor',
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_cost NUMERIC(10, 4) DEFAULT 0.0000,
    status VARCHAR(50) NOT NULL DEFAULT 'initializing',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);
CREATE INDEX idx_agent_runs_task_agent ON agent_runs(task_id, agent_id);

-- 10. TOOL EXECUTIONS TABLE
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    result_output TEXT,
    exit_code INT DEFAULT 0,
    execution_duration_ms INT NOT NULL,
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tool_exec_agent_run ON tool_executions(agent_run_id);

-- 11. MEMORIES TABLE
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    memory_type VARCHAR(50) NOT NULL, -- short_term, long_term, project, global
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    relevance_score NUMERIC(3,2) DEFAULT 1.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_memories_tenant_type ON memories(tenant_id, memory_type);
CREATE INDEX idx_memories_project ON memories(project_id);

-- 12. MEMORY EMBEDDINGS TABLE
CREATE TABLE memory_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL, -- OpenAI text-embedding-3-small dimension
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_memory_embeddings_hnsw ON memory_embeddings 
USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- 13. AUDIT LOGS TABLE
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL, -- User UUID or Agent UUID
    actor_type VARCHAR(50) NOT NULL, -- user, agent, system
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID NOT NULL,
    ip_address INET,
    changes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_tenant_action ON audit_logs(tenant_id, action);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);

-- 14. API KEYS TABLE
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    key_prefix VARCHAR(16) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    scopes JSONB NOT NULL DEFAULT '["read", "write"]'::jsonb,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- 15. PLUGINS TABLE
CREATE TABLE plugins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_plugin_tenant_name ON plugins(tenant_id, name);

-- 16. COST LEDGER TABLE
CREATE TABLE cost_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    model_provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    input_tokens INT NOT NULL,
    output_tokens INT NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_cost_ledger_tenant_project ON cost_ledger(tenant_id, project_id);
CREATE INDEX idx_cost_ledger_recorded ON cost_ledger(recorded_at DESC);
```

---

### Memory System

The AegisOS Memory System mimics human cognitive architecture, providing agents with context persistence across four distinct memory tiers.

```
+---------------------------------------------------------------------------------------------------+
|                                  AEGISOS MULTI-TIER MEMORY SYSTEM                                 |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  +---------------------------------------+     +-----------------------------------------------+  |
|  | 1. SHORT-TERM MEMORY (Ephemeris)      |     | 2. LONG-TERM MEMORY (Agent Episodic)          |  |
|  | - Execution Context Window            |     | - Past Problem Solving Trajectories           |  |
|  | - Active Tool Outputs & Scratchpad    |     | - Refactoring Fix Patterns & Learned Lessons  |  |
|  | - In-Memory Sliding Redis Window      |     | - Stored in Vector DB + Postgres Metadata     |  |
|  +---------------------------------------+     +-----------------------------------------------+  |
|                                                                                                   |
|  +---------------------------------------+     +-----------------------------------------------+  |
|  | 3. PROJECT MEMORY (Context Index)     |     | 4. GLOBAL MEMORY (Knowledge Commons)          |  |
|  | - AST Codebase Knowledge Graph        |     | - Standard Framework Conventions              |  |
|  | - Repository Architecture Constraints |     | - Vulnerability Patterns (CVE Resolutions)    |  |
|  | - Git History & Commit Summaries      |     | - Cross-Project Shared Tool Recipes           |  |
|  +---------------------------------------+     +-----------------------------------------------+  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Memory Tiers Breakdown

1. **Short-Term Memory:** Ephemeral scratchpad storing active conversation tokens and tool outputs. When short-term context exceeds 75% of model context limits (e.g., 96k tokens of 128k), an automated background worker generates a compressed recursive summary, persisting raw context to Long-Term memory and clearing context space.
2. **Long-Term Memory:** Episodic memory tracking agent experiences across tasks. If an agent previously resolved a complex bug involving `FastAPI async deadlocks`, the fix trajectory is indexed for future retrieval.
3. **Project Memory:** Contextual index of the target software project containing AST maps, dependency graphs, framework choices, and coding conventions.
4. **Global Memory:** Multi-tenant shared knowledge base (sanitized) providing static language specs, security best practices, and standard library references.

#### Semantic Memory Retrieval Strategy (Hybrid RAG Pipeline)

To maximize relevance and eliminate LLM hallucinations, memory retrieval utilizes a 4-stage Hybrid RAG pipeline:

```
Query Input ---> [ Sparse BM25 Search ] ---            ---> [ Dense Vector Search ] ----> [ Reciprocal Rank Fusion ] ---> [ Cross-Encoder Reranker ] ---> Top-K Context
```

```python
# Hybrid Memory Retrieval Strategy Algorithm
import numpy as np

def hybrid_memory_retrieval(query_text: str, project_id: str, top_k: int = 5) -> list:
    # 1. Generate Query Vector Embedding
    query_vector = embedding_client.embed(query_text)
    
    # 2. Execute Dense Vector Search (pgvector HNSW)
    dense_results = db.query(
        "SELECT memory_id, COSINE_SIMILARITY(embedding, :q_vec) as score "
        "FROM memory_embeddings WHERE project_id = :p_id ORDER BY score DESC LIMIT 20",
        {"q_vec": query_vector, "p_id": project_id}
    )
    
    # 3. Execute Sparse Lexical Search (PostgreSQL tsvector / BM25)
    sparse_results = db.query(
        "SELECT id as memory_id, ts_rank(to_tsvector('english', content), plainto_tsquery(:q)) as score "
        "FROM memories WHERE project_id = :p_id ORDER BY score DESC LIMIT 20",
        {"q": query_text, "p_id": project_id}
    )
    
    # 4. Apply Reciprocal Rank Fusion (RRF)
    rrf_scores = {}
    k_constant = 60
    for rank, item in enumerate(dense_results):
        rrf_scores[item.memory_id] = rrf_scores.get(item.memory_id, 0) + (1.0 / (k_constant + rank + 1))
    for rank, item in enumerate(sparse_results):
        rrf_scores[item.memory_id] = rrf_scores.get(item.memory_id, 0) + (1.0 / (k_constant + rank + 1))
        
    # 5. Fetch Candidate Memory Records
    candidate_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:15]
    candidates = db.fetch_memories_by_ids(candidate_ids)
    
    # 6. Final Cross-Encoder Reranking
    final_ranked_memories = cross_encoder_reranker.rank(query_text, candidates, limit=top_k)
    return final_ranked_memories
```

---

### Event Bus Architecture

AegisOS relies on an asynchronous event-driven architecture to communicate system actions, trigger workflow steps, and broadcast agent status changes.

#### Technology Selection & Justification

AegisOS selects **NATS JetStream** as its enterprise event bus, backed by **Redis Streams** for single-server zero-dependency modes.

| Event Bus | NATS JetStream | Apache Kafka | Redis Pub/Sub | Justification for NATS JetStream |
| :--- | :--- | :--- | :--- | :--- |
| **Footprint / Memory** | Minimal (~20MB binary) | Heavy (Requires JVM / ZooKeeper / KRaft) | Extremely Light | NATS boots instantly in single-node environments while providing native clustering for enterprise scale. |
| **Persistence** | Native file/memory storage | Native file log | Volatile (unless using Redis Streams) | Guarantees message delivery across agent process restarts. |
| **Subject Wildcard Routing** | Superior (`aegis.agent.*.completed`) | Topic-based only | Pattern-based | Enables fine-grained consumer event filtering across tenants and projects. |

#### Event Schema Standard (CloudEvents 1.0 JSON)

All event payloads strictly adhere to the CloudEvents 1.0 specification:

```json
{
  "specversion": "1.0",
  "type": "aegis.agent.action.executed.v1",
  "source": "/aegis/agent-runtime/aen-node-04",
  "id": "evt-77a8b9c0-1234-5678-90ab-cdef12345678",
  "time": "2026-08-05T08:46:00Z",
  "datacontenttype": "application/json",
  "tenant_id": "tenant-uuid-1111",
  "data": {
    "task_id": "task-uuid-2222",
    "agent_id": "agent-uuid-3333",
    "tool_name": "execute_unit_tests",
    "parameters": {
      "framework": "pytest",
      "test_path": "tests/unit/test_auth.py"
    },
    "result": {
      "exit_code": 0,
      "passed": 12,
      "failed": 0,
      "duration_ms": 1420
    },
    "token_cost_usd": 0.0034
  }
}
```

---

### Authentication & Authorization

Security in AegisOS is structured around zero-trust multi-tenancy, strict cryptographic identity verification, and fine-grained Attribute-Based Access Control (ABAC).

#### Authentication Strategy

1. **User Authentication:** OAuth 2.0 + OpenID Connect (OIDC) integrations for GitHub, GitLab, Google Workspace, and enterprise SAML SSO.
2. **Session Token Tokens:**
   - **Access Tokens:** Short-lived JWTs (15-minute expiration) signed via RS256 algorithm containing tenant and role claims.
   - **Refresh Tokens:** Long-lived HTTP-only, Secure, SameSite=Strict cookies stored in Redis with revocation checks.
3. **Machine/CLI API Keys:** Formatted as `aegis_live_` followed by 32 cryptographically secure random bytes. Stored as SHA-256 hashes in PostgreSQL; original keys are displayed exactly once upon generation.

#### RBAC & ABAC Security Matrix

Role-Based Access Control (RBAC) defines static role boundaries, enforced via dynamic Attribute-Based Access Control (ABAC) evaluation policies:

```
+--------------------------------------------------------------------------------------------------+
|                                    ACCESS CONTROL MATRIX (RBAC)                                  |
+--------------------------------------------------------------------------------------------------+
| Role              | View Project | Create Task | Approve Privileged Tool | Manage Tenant / Billing |
+-------------------+--------------+-------------+-------------------------+-----------------------+
| TenantOwner       | YES          | YES         | YES                     | YES                   |
| ProjectMaintainer | YES          | YES         | YES                     | NO                    |
| Developer         | YES          | YES         | NO (Requires Lead)      | NO                    |
| AgentOperator     | YES          | YES         | YES                     | NO                    |
| Auditor           | READ-ONLY    | NO          | NO                      | NO                    |
+--------------------------------------------------------------------------------------------------+
```

```python
# ABAC Evaluation Policy Engine Example
def evaluate_abac_permission(user: User, action: str, resource: Resource) -> bool:
    # Rule 1: Strict Multi-Tenant Isolation
    if user.tenant_id != resource.tenant_id:
        return False
        
    # Rule 2: Privileged Infrastructure Safeguard
    if action == "tool:execute:cloud_deploy":
        if user.role not in ["TenantOwner", "ProjectMaintainer"]:
            return False
        if resource.environment == "production" and not resource.has_passed_security_audit:
            return False
            
    # Rule 3: Budget Cap Governance
    if action == "agent:task:start" and resource.project.monthly_cost > resource.project.budget_cap:
        return False
        
    return True
```

---

### Plugin & Extension System

AegisOS provides an extensible microkernel framework that allows third-party developers to register custom domain tools, novel LLM provider connectors, memory vector stores, and custom project adapters.

#### Architecture and SDK Surface

Plugins are executed as standalone, isolated modules that register capabilities via the AegisOS Plugin SDK interface:

```typescript
// AegisOS TypeScript Plugin Extension Interface
import { IAegisPlugin, ToolDefinition, Context } from '@aegisos/sdk';

export class SolanaAnchorPlugin implements IAegisPlugin {
  id = 'plugin-solana-anchor';
  version = '1.0.0';

  async register(context: Context): Promise<void> {
    context.registerTool({
      name: 'anchor_test_run',
      description: 'Compiles and executes Solana Anchor smart contract tests in local ledger',
      permissionTier: 'WORKSPACE_WRITE',
      execute: async (params, sandbox) => {
        const result = await sandbox.exec('anchor test', { cwd: params.workspacePath });
        return { exitCode: result.exitCode, output: result.stdout };
      }
    });
  }
}
```

#### Plugin Sandboxing (WebAssembly / Micro-Containers)

Third-party plugin code runs in a zero-trust environment:

* **Wasm Runtime Isolation:** Plugins written in Rust/TypeScript compile to WebAssembly (Wasm) and run within a `Wasmtime` sandbox with explicitly capped memory and CPU limits.
* **Micro-Container Isolation:** Heavy plugins requiring native dependencies run in ephemeral Tier 2 gVisor sandboxes with network interface restrictions.

---

### API Gateway

The API Gateway acts as the secure entry point for all external client traffic, routing incoming requests, terminating TLS, and enforcing access rules.

#### Technology Choice: Traefik v3

AegisOS standardizes on **Traefik v3** (with FastAPI Gateway middleware fallback for single-node setups). Traefik offers automatic TLS certificate management via Let's Encrypt (ACME), native Docker socket discovery, dynamic routing, and minimal latency overhead (<1ms).

```
+---------------------------------------------------------------------------------------------------+
|                                     API GATEWAY ROUTING SCHEME                                    |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  Client Request                                                                                   |
|        |                                                                                          |
|        v                                                                                          |
|  +---------------------------------------------------------------------------------------------+  |
|  | TRAEFIK V3 API GATEWAY                                                                      |  |
|  | - TLS Termination (ECDSA P-256)                                                             |  |
|  | - DDoS IP Rate Limiter (Redis Sliding Window: 100 req/min)                                  |  |
|  +----------------------------------------------+----------------------------------------------+  |
|                                                 |                                                 |
|         +---------------------------------------+---------------------------------------+         |
|         | Path: /api/v1/*                                                               | Path: /ws/* or /api/v1/agent/stream
|         v                                                                               v         |
|  +---------------------------------------------+                               +------------------+
|  | REST Core Backend Services (FastAPI)        |                               | SSE / WebSocket  |
|  | [ Authentication & Authorization Verification ] |                               | Streaming Engine |
|  +---------------------------------------------+                               +------------------+
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Rate Limiting & Versioning Policies

* **Sliding Window Rate Limiter:** Backed by Redis, tracking request counts per IP and API Key prefix (`aegis:ratelimit:{key_prefix}`).
* **API Versioning Standard:** Path-based versioning (`/api/v1/`, `/api/v2/`). Deprecated endpoints emit standardized HTTP response headers (`Deprecation: @1778025600`, `Sunset: @1780617600`) adhering to RFC 8594.

---

### Observability Architecture

Comprehensive observability across logs, metrics, distributed traces, and security audits guarantees operational clarity and prompt failure triage.

```
+---------------------------------------------------------------------------------------------------+
|                                 OPEN TELEMETRY OBSERVABILITY STACK                                |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  +---------------------------+   +---------------------------+   +-----------------------------+  |
|  |     STRUCTURED LOGS       |   |    PROMETHEUS METRICS     |   |     DISTRIBUTED TRACES      |  |
|  |    (OpenTelemetry JSON)   |   |   (Exposed on /metrics)   |   |    (OTLP / Jaeger / Tempo)  |  |
|  | - tenant_id               |   | - active_agents_count     |   | - Gateway Request Span      |  |
|  | - project_id              |   | - llm_token_throughput    |   | - Orchestrator Plan Span    |  |
|  | - agent_run_id            |   | - sandbox_execution_time  |   | - Agent Sandbox Exec Span   |  |
|  | - trace_id & span_id      |   | - task_failure_rates      |   | - LLM Vendor Call Span      |  |
|  +---------------------------+   +---------------------------+   +-----------------------------+  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Metrics Exporter Specification

Key Prometheus metrics emitted by the AegisOS system:

* `aegis_active_agents_total{tenant_id, role}` - Gauge tracking active executing agents.
* `aegis_llm_token_consumption_total{provider, model, type}` - Counter measuring input/output token usage.
* `aegis_task_execution_duration_seconds{status, priority}` - Histogram measuring end-to-end task duration.
* `aegis_sandbox_circuit_breaker_tripped_total{reason}` - Counter tracking safety interventions.

---

### Scalability Strategy

AegisOS is architected to transition seamlessly from a single bare-metal server deployment to an enterprise multi-region Kubernetes cluster.

```
+---------------------------------------------------------------------------------------------------+
|                                 VERTICAL TO HORIZONTAL SCALING ROADMAP                            |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  SINGLE-SERVER DEPLOYMENT (Phase 1)                ENTERPRISE MULTI-CLUSTER DEPLOYMENT (Phase 2)  |
|  +------------------------------------+            +-------------------------------------------+  |
|  | - 1x Bare Metal (64-core, 256GB) |            | - Traefik Load Balancer Ingress Cluster   |  |
|  | - Embedded Postgres 16 + pgvector  |  ------->  | - Stateless FastAPI Pod Autoscaling (HPA) |  |
|  | - Local Redis 7 & NATS JetStream   |            | - Distributed Temporal & Worker Nodes     |  |
|  | - Local gVisor Sandbox Pool        |            | - AWS Aurora Postgres + Qdrant Cluster    |  |
|  +------------------------------------+            +-------------------------------------------+  |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

#### Single-Server Optimization Matrix

To maximize single-server resource utilization, AegisOS enforces:

1. **Async IO Event Loop:** Running FastAPI under `uvloop` with `httpx` connection pooling for non-blocking network calls.
2. **PostgreSQL Memory Tuning:** Shared buffers set to 25% system RAM, `work_mem` configured for efficient vector indexing.
3. **Pre-Warmed Sandbox Pool:** Maintaining 5 pre-warmed gVisor container sandboxes to eliminate execution startup latency.

#### Multi-Server Horizontal Scaling Matrix

When scaling horizontally:

1. **Stateless API Web Nodes:** Scaled out horizontally behind Traefik ingress.
2. **Temporal Worker Pods:** Auto-scaled independently based on temporal queue depth and CPU saturation.
3. **Database Sharding:** PostgreSQL scaled via read-replicas for query offloading, or Citus extension for multi-tenant table sharding.

---

### Disaster Recovery & High Availability

AegisOS provides high availability and disaster recovery guarantees suitable for mission-critical enterprise environments.

#### Backup Strategy

* **Transactional Database Backups:** Automated continuous Write-Ahead Log (WAL) archiving to encrypted S3 object storage via `pgBackRest`. Nightly full physical database backups with a 30-day retention policy.
* **Vector Index & Memory Backups:** Daily snapshots of Qdrant vector collections and `pgvector` index states exported to S3.
* **Workspace Directory Snapshots:** Incremental git bundle backups of all local project workspaces taken prior to agent batch modifications.

#### High Availability & Failover Design

* **PostgreSQL HA Pair:** Managed Patroni cluster with Etcd leader election and automatic failover within 10 seconds.
* **Stateless Service Auto-Healing:** Kubernetes Liveness and Readiness probes automatically restart stalled API backend or worker pods.

#### Recovery Targets (RTO & RPO)

```
+---------------------------------------------------------------------------------------------------+
|                                 DISASTER RECOVERY TARGET METRICS                                  |
+---------------------------------------------------------------------------------------------------+
| Service Tier               | Recovery Time Objective (RTO) | Recovery Point Objective (RPO)       |
+----------------------------+-------------------------------+--------------------------------------+
| Core API & Database        | < 15 Minutes                  | < 1 Minute (WAL Archiving)           |
| Task Queue & Temporal State| < 5 Minutes                   | 0 Seconds (Event-Sourced Persistence)|
| Vector Memory DB           | < 30 Minutes                  | < 15 Minutes                         |
| Agent Sandbox Execution    | < 1 Minute (Re-provision)     | 0 Seconds (Stateless Replay)         |
+---------------------------------------------------------------------------------------------------+
```

---

### Universal Project Adaptation Engine

AegisOS adapts its agent tools, compiler toolchains, verification suites, and deployment pathways based on the detected **Project Type**:

```
+---------------------------------------------------------------------------------------------------+
|                               UNIVERSAL PROJECT ADAPTATION MATRIX                                 |
+---------------------------------------------------------------------------------------------------+
| Project Type   | Primary Agents Installed    | Compiler & Sandbox Tools    | Verification Suite   |
+----------------+-----------------------------+-----------------------------+----------------------+
| Web App        | Frontend, Backend, QA       | Node.js, Vite, Next, Python | Playwright, Jest, ESLint |
| Mobile App     | Mobile Spec, UI/UX, QA      | Flutter, React Native, Swift| Detox, XCTest, Flutter Test |
| Blockchain     | Smart Contract, Auditor     | Hardhat, Foundry, Anchor    | Slither, Certora, Echidna |
| Machine Learn  | Data Eng, ML Architect, QA  | PyTorch, CUDA, MLflow, Ray  | pytest, Great Expectations |
| Microservices  | DevOps, Backend, SecOps     | Docker, Go, Rust, Helm      | k6, SonarQube, Trivy |
+---------------------------------------------------------------------------------------------------+
```

This universal capability guarantees that AegisOS can manage complex heterogeneous repositories seamlessly—from smart contract backends paired with Flutter frontends to high-performance C++ ML execution nodes—delivering end-to-end autonomous engineering at enterprise standard.
