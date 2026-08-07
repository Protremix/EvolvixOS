# Document 7: AI ARCHITECTURE

## 1. LLM Integration Layer

### 1.1 Multi-Provider LLM Abstraction Architecture
AegisOS employs an enterprise-grade LLM Integration Layer that decouples high-level agent reasoning from concrete LLM provider implementations. The primary model for reasoning, planning, code generation, and complex structural tasks is OpenAI's GPT-4o. However, to guarantee high availability, operational resilience, and compliance with varying cloud/on-premise governance policies, the integration layer provides an asynchronous unified interface across OpenAI, Anthropic, and self-hosted vLLM/Ollama endpoints.

```
+-------------------------------------------------------------------------------+
|                             AegisOS Agent Runtime                             |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                          LLM Gateway & Router Interface                        |
+-------------------------------------------------------------------------------+
     |                                  |                                  |
     v                                  v                                  v
+------------------------+  +------------------------+  +------------------------+
| OpenAI Client Adapter  |  | Anthropic Adapter      |  | vLLM / Ollama Adapter  |
| (GPT-4o / GPT-4o-mini) |  | (Claude 3.5 Sonnet)    |  | (DeepSeek-R1/Llama-3.3)|
+------------------------+  +------------------------+  +------------------------+
     |                                  |                                  |
     +----------------------------------+----------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|          Token Budgeting, Rate Limiting, Caching & Telemetry Engine           |
+-------------------------------------------------------------------------------+
```

The unified interface is defined via an abstract base class `BaseLLMClient` implemented in Python (`asyncio`). It standardizes request structures, tool definitions, response schemas, usage metadata, and streaming callbacks across all providers.

```python
import abc
import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional

class LLMResponse:
    def __init__(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        finish_reason: str = "stop",
        model_name: str = ""
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.finish_reason = finish_reason
        self.model_name = model_name

class BaseLLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout: float = 60.0
    ) -> LLMResponse:
        pass

    @abc.abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        timeout: float = 60.0
    ) -> AsyncGenerator[str, None]:
        pass
```

### 1.2 Streaming vs. Asynchronous Batch Processing
AegisOS distinguishes between two primary execution paths for LLM interaction:
1. **Interactive / Real-time Execution (Streaming)**: Used when agents are executing interactive workflows (e.g., interactive CLI sessions, user feedback loops, or real-time file editing). Responses are streamed via Server-Sent Events (SSE) or WebSockets using `generate_stream()`. First-token latency (TTFT) is optimized to remain under 600ms.
2. **Background / Bulk Processing (Batch Execution)**: Used for heavy asynchronous tasks such as deep code repository analysis, bulk unit test generation, architectural reviews, and static security scans. These tasks utilize OpenAI's Batch API or parallel background workers with higher batch concurrency, reducing API costs by 50% and circumventing strict rate-limit bursts.

### 1.3 Resilience, Retry Logic, and Timeout Handling
To prevent transient API errors or rate limiting (HTTP 429) from halting software engineering workflows, the integration layer implements an exponential backoff retry strategy with decorrelated jitter.
- **Retryable Errors**: HTTP status codes 429 (Rate Limit), 500, 502, 503, 504, network connection resets, and timeout exceptions.
- **Non-Retryable Errors**: HTTP status codes 400 (Bad Request - e.g., invalid prompt format), 401/403 (Authentication/Authorization failure), 404 (Model not found), context window overflow errors.
- **Backoff Algorithm**:
  $$	ext{Delay} = \min(	ext{max\_delay}, 	ext{base\_delay} 	imes 2^{	ext{attempt}} + 	ext{uniform}(0, 	ext{jitter}))$$
  Where `base_delay` = 1.0s, `max_delay` = 30.0s, and maximum attempts = 5.

### 1.4 Prompt Management & Template Registry
Prompts in AegisOS are treated as core version-controlled software assets stored in a centralized Prompt Registry (`/prompts/v1/`). Prompts are constructed using Jinja2 templating, enforcing strict separation between logic and instructions.
- **Versioning**: Prompts follow Semantic Versioning (e.g., `architect_system_v1.2.0.jinja2`).
- **Template Inheritance**: Base safety guardrails, format constraints, and tool invocation instructions are inherited from `base_system_prompt.jinja2`.
- **Validation**: Every prompt template undergoes CI validation using unit tests that assert expected output JSON schemas and tool binding compatibility.

### 1.5 Token Budgeting and Tracking System
To maintain financial control and prevent runaway execution loops, AegisOS enforces a strict multi-tier Token Budgeting System:
- **Global Organization Limits**: Hard monthly and daily USD ceiling enforced via Redis sliding-window counters.
- **Project-Level Budgets**: Max token cap per project (e.g., 10,000,000 tokens per feature lifecycle).
- **Task-Level Limits**: Max tokens allocated per single agent task execution (e.g., 100,000 tokens).
- **Dynamic Allocation Engine**: Automatically allocates max generation tokens based on task complexity (e.g., complex code generation receives 4,096 tokens, while single classification calls receive 256 tokens).

---

## 2. Agent Orchestration Engine

### 2.1 Task Assignment and Directed Acyclic Graph (DAG) Execution
The AegisOS Orchestration Engine manages software project execution by decomposing high-level engineering tasks into a Directed Acyclic Graph (DAG). Nodes in the DAG represent specific agent actions (e.g., write spec, generate code, run unit tests, security scan), while directed edges represent execution dependencies.

```
                      +-------------------+
                      | Product Owner     |
                      | Spec Generation   |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      | Architect Agent   |
                      | Architecture ADR  |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      | Tech Lead Agent   |
                      | DAG Decomposition |
                      +-------------------+
                                |
         +----------------------+----------------------+
         |                                             |
         v                                             v
+------------------+                          +------------------+
| Engineer Agent 1 |                          | Engineer Agent 2 |
| Component A Code |                          | Component B Code |
+------------------+                          +------------------+
         |                                             |
         +----------------------+----------------------+
                                |
                                v
                      +-------------------+
                      | QA Engineer Agent |
                      | Integration Tests |
                      +-------------------+
                                |
                                v
                      +-------------------+
                      | DevOps Agent      |
                      | Deploy / CI Check |
                      +-------------------+
```

### 2.2 Dependency Resolution & Topological Sorting
The orchestrator maintains the runtime status of the DAG using Kahn's algorithm for topological sorting.
- **State Machine Nodes**: Task nodes transition through states: `PENDING` -> `BLOCKED` -> `READY` -> `RUNNING` -> `COMPLETED` / `FAILED`.
- **Dynamic Graph Mutation**: Tech Lead and Architect agents can dynamically mutate the DAG at runtime (e.g., adding a bug-fix sub-task if QA tests fail).
- **Blocking State Resolution**: When a task completes successfully, the orchestrator evaluates dependent child nodes. If all parent dependencies for a node reach `COMPLETED`, the node status transitions to `READY` and is enqueued in the Redis Priority Queue.

### 2.3 Priority Queues and Capability Matching
Tasks in the `READY` state are placed into Redis-backed Priority Queues:
- **Priority Tiers**: `CRITICAL` (P0 - Security fixes, system outages), `HIGH` (P1 - Core feature dependencies), `NORMAL` (P2 - Standard tasks), `LOW` (P3 - Documentation, non-blocking refactoring).
- **Capability Matching**: Tasks specify required capabilities (e.g., `["python", "docker", "postgres", "gpu"]`). The orchestrator matches tasks to available agent worker instances whose capability profile matches or supersedes the task requirement.

### 2.4 Parallel Execution and Concurrency Control
- **Worker Pools**: AegisOS executes agents inside isolated process pools managed by Celery/AsyncIO worker nodes.
- **Resource Limits**: Concurrency per project is capped (default: 8 parallel agents per project) to avoid API rate-limiting and filesystem/git branch collision.
- **Thread & Memory Isolation**: Each agent process runs in an isolated workspace container with filesystem namespace isolation.

---

## 3. Agent Communication Protocol

### 3.1 Event Bus Architecture
Agent communication in AegisOS is completely asynchronous and event-driven, built on Redis Pub/Sub for real-time messaging combined with Redis Streams for persistent event logging and message replay.

```
+-------------------------------------------------------------------------------+
|                            Redis Pub/Sub Event Bus                            |
+-------------------------------------------------------------------------------+
    |                  |                      |                      |
    v                  v                      v                      v
[aegis.events.  [aegis.events.         [aegis.events.        [aegis.events.
 <proj>.po]      <proj>.architect]      <proj>.techlead]       <proj>.dev]
    |                  |                      |                      |
    +------------------+----------------------+----------------------+
                                |
                                v
+-------------------------------------------------------------------------------+
|                       Redis Stream Persistence Ledger                         |
+-------------------------------------------------------------------------------+
```

### 3.2 Topic Naming Convention
Topics follow a standardized hierarchical namespace:
`aegis.events.<project_id>.<agent_role>.<event_type>`

Examples:
- `aegis.events.prj_9821.architect.adr_approved`
- `aegis.events.prj_9821.developer.code_generated`
- `aegis.events.prj_9821.qa.test_failed`

### 3.3 Standard Event Schemas & Message Types
All messages sent across the event bus conform to JSON Schemas defining five core message types:

#### Message Type Schemas
1. **Command Message**: Directive instructing a target agent to perform an action.
2. **Event Message**: Notification broadcasting a state change or artifact creation.
3. **Query Message**: Request for information or state from another agent.
4. **Response Message**: Reply to a Query Message.
5. **Broadcast Message**: System-wide announcement (e.g., project paused, HITL required).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AegisOSAgentMessage",
  "type": "object",
  "properties": {
    "message_id": { "type": "string", "format": "uuid" },
    "correlation_id": { "type": "string", "format": "uuid" },
    "project_id": { "type": "string" },
    "sender": {
      "type": "object",
      "properties": {
        "agent_id": { "type": "string" },
        "agent_role": { "type": "string" }
      },
      "required": ["agent_id", "agent_role"]
    },
    "recipient": {
      "type": "object",
      "properties": {
        "agent_id": { "type": "string" },
        "agent_role": { "type": "string" }
      },
      "required": ["agent_role"]
    },
    "message_type": {
      "type": "string",
      "enum": ["COMMAND", "EVENT", "QUERY", "RESPONSE", "BROADCAST"]
    },
    "event_name": { "type": "string" },
    "timestamp": { "type": "string", "format": "date-time" },
    "payload": { "type": "object" },
    "metadata": {
      "type": "object",
      "properties": {
        "token_usage": { "type": "integer" },
        "execution_time_ms": { "type": "number" }
      }
    }
  },
  "required": ["message_id", "correlation_id", "project_id", "sender", "recipient", "message_type", "event_name", "timestamp", "payload"]
}
```

---

## 4. Agent Health Monitoring

### 4.1 Heartbeat Mechanism
Every active agent process emits a periodic heartbeat signal to Redis every 10 seconds:
- Key: `aegis:heartbeat:<project_id>:<agent_id>`
- Payload: `{"status": "WORKING", "current_task_id": "tsk_104", "memory_mb": 245.2, "last_active": "2026-08-05T08:50:00Z"}`
- Key Expiry (TTL): 30 seconds.

### 4.2 Failure Detection Architecture
An Orchestrator Health Monitor process periodically queries agent heartbeats:
- **Liveness Failure**: If an agent's heartbeat key expires (missing 3 consecutive pings / 30 seconds), it is marked as `UNRESPONSIVE`.
- **Stall Detection**: If an agent is in `WORKING` state on the same task without progress updates or token stream output for over 10 minutes, the orchestrator triggers a task timeout probe.
- **Crash Detection**: Unhandled process exits report non-zero exit codes to the supervisor process, triggering instant failure alerts.

### 4.3 Automated Recovery & Self-Healing
When an agent failure is detected:
1. **State Snapshot Retrieval**: The system reads the last valid state checkpoint stored in PostgreSQL / Redis for that task.
2. **Worker Respawn**: The Orchestrator terminates the dead container/process and spawns a fresh agent instance.
3. **Context Restoration**: The new agent receives the exact correlation ID, task graph node, and last saved workspace patch.
4. **Dead Letter Queue (DLQ)**: If an agent fails on the same task 3 times sequentially, the task is moved to the Project Dead Letter Queue, blocking dependent DAG nodes and raising an alert for Human-in-the-Loop intervention.

---

## 5. Agent Scaling & Load Balancing

### 5.1 Dynamic Agent Spawning
AegisOS employs dynamic pod/container scaling on Kubernetes or Docker Swarm:
- **Scale-Up Trigger**: When the queue depth for `READY` tasks exceeds available agent worker capacity, or when high-priority tasks (P0/P1) enter the queue.
- **Container Isolation**: Each agent worker pod runs with strict resource limits (e.g., 2 vCPU, 4GB RAM, ephemeral storage limit 20GB).

```
+-------------------------------------------------------------------------------+
|                            K8s Auto-Scaler Engine                             |
+-------------------------------------------------------------------------------+
                                        |
                 +----------------------+----------------------+
                 | (Queue Depth > 10)                          | (Idle > 300s)
                 v                                             v
+----------------------------------+          +----------------------------------+
| Provision Agent Worker Pod       |          | Gracefully Terminate Agent Pod   |
| Mount Project Filesystem Volume  |          | Flush Local Caches to Postgres   |
+----------------------------------+          +----------------------------------+
```

### 5.2 Work-Stealing Load Balancing
To maximize throughput and prevent worker starvation:
- Agent workers maintain local worker queues.
- When an agent completes its assigned task and its local queue becomes empty, it executes a **Work-Stealing Algorithm** to steal unassigned `READY` tasks from higher-level project queues.
- Lock contention is prevented using Redis distributed locks (`Redlock`).

---

## 6. Prompt Engineering Framework

### 6.1 Template Hierarchy & Context Pipeline
Prompts are constructed dynamically through a 4-layer composition pipeline:

```
+-------------------------------------------------------------------------------+
| Layer 1: Universal Base System Prompt (Safety, Tool Syntax, JSON Output Rules) |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Layer 2: Role-Specific System Prompt (e.g., Senior Architect Persona)         |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Layer 3: Dynamic Context Injection (RAG Memory, Workspace Diff, File Tree)    |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Layer 4: Task Instructions & Few-Shot Examples (Target Task Payload)          |
+-------------------------------------------------------------------------------+
```

### 6.2 Dynamic Context Injection Pipeline
Before dispatching a prompt to GPT-4o, the context engine builds the prompt payload:
1. **Workspace AST & File Tree**: Injects compact file structure representation.
2. **Active Code Diffs**: Injects git diffs relevant to current task.
3. **RAG Vector Memory**: Performs cosine similarity search over vector DB to inject relevant historical ADRs, code snippets, or API specs.
4. **Budget Trimming**: Truncates context if total tokens exceed 80% of model window using a priority-preserving sliding window.

### 6.3 Few-Shot Example Retrieval
Few-shot examples are dynamically retrieved from the Global Memory vector store based on semantic task similarity. Rather than hardcoding fixed examples, the system queries:
$$	ext{Query} = 	ext{Embedding}(	ext{task\_description} + 	ext{programming\_language})$$
The top 2 highest-scoring historical success traces (input task + generated code + passed tests) are injected into the prompt.

---

## 7. LLM Fallback Strategy

### 7.1 Multi-Tier Provider Fallback Chain
To ensure 99.99% system availability despite upstream LLM outages or degradation, AegisOS enforces an automated multi-tier fallback hierarchy:

```
+-------------------------------------------------------------------------------+
| Tier 1 Primary: OpenAI GPT-4o (Full Reasoning & Tool Capabilities)           |
+-------------------------------------------------------------------------------+
                                        | (On 5xx Error / Rate Limit / Timeout)
                                        v
+-------------------------------------------------------------------------------+
| Tier 2 Secondary: Anthropic Claude 3.5 Sonnet (High Code & Analysis Quality)  |
+-------------------------------------------------------------------------------+
                                        | (On Anthropic Outage)
                                        v
+-------------------------------------------------------------------------------+
| Tier 3 Fallback: Self-Hosted DeepSeek-R1 / Llama-3.3-70B on vLLM Cluster       |
+-------------------------------------------------------------------------------+
```

### 7.2 Circuit Breaker Pattern
Each LLM provider adapter is wrapped in a Circuit Breaker state machine:
- **Closed State**: Normal operations. Requests route to Primary (GPT-4o).
- **Open State**: If 5 consecutive failures occur within a 60-second window, the circuit opens for 300 seconds. All traffic immediately bypasses GPT-4o and routes to Tier 2 (Claude 3.5 Sonnet).
- **Half-Open State**: After 300 seconds, a probe request is sent to GPT-4o. If successful, the circuit closes; if it fails, the open timer resets.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 300.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = asyncio.get_event_loop().time()

    async def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = asyncio.get_event_loop().time()

    async def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        now = asyncio.get_event_loop().time()
        if self.state == "OPEN":
            if now - self.last_state_change >= self.recovery_timeout:
                self.state = "HALF-OPEN"
                return True
            return False
        return True
```

---

## 8. Token Cost Optimization

### 8.1 Multi-Tier Prompt Caching
To minimize API expenditure, AegisOS deploys a two-tier caching architecture:
1. **Exact-Match Redis Cache**: Hashes system prompt + user instructions using SHA-256. If exact match exists with valid TTL, cached response returns instantly (0 API cost, <5ms latency).
2. **Semantic Prompt Cache**: Uses pgvector/Chroma to calculate vector similarity between incoming prompts and historical cached prompts. If cosine similarity > 0.96 and workspace state hash matches, the cached response is re-used.

### 8.2 Context Compression Algorithms
Large code repositories can easily exhaust token budgets. AegisOS employs three compression techniques:
- **AST Tree Pruning**: Strips function bodies from non-target source files, leaving only class signatures, docstrings, and function signatures.
- **Unified Diff Context**: Injects only `git diff` chunks instead of entire 2,000-line code files.
- **Summarized Turn History**: Older conversation turns in agent memory are automatically summarized into bulleted factual representations by a lightweight model (`gpt-4o-mini`).

---

## 9. Agent Evaluation Framework

### 9.1 Multi-Dimensional Quality Metrics
AegisOS evaluates agent generation quality continuously using automated metric scoring:
1. **Code Compilation Rate**: Binary score (1/0) indicating syntactically valid code execution.
2. **Unit Test Pass Rate**: Percentage of generated/existing unit tests passing against output code.
3. **AST Syntax Validity**: Verification of valid Abstract Syntax Tree generation.
4. **Architectural Compliance Score**: Automated check verifying code adherence to project structure and static import rules.

### 9.2 Automated LLM-as-a-Judge Panel
For qualitative tasks (e.g., PRDs, ADRs, Code Review feedback), AegisOS invokes an independent LLM-as-a-Judge evaluation workflow:
- **Evaluation Rubric**: Evaluates outputs across 5 dimensions: Correctness, Completeness, Security, Maintainability, and Clarity.
- **Scoring Scale**: Grade 1-5 with detailed reasoning output required.
- **Threshold Gate**: Outputs scoring below 3.5 are automatically rejected and sent back to the generating agent with critique annotations.

---

## 10. Human-in-the-Loop (HITL) Integration

### 10.1 Risk Tiering Matrix
To balance autonomy with safety, AegisOS categorizes operations into risk levels:

| Risk Tier | Operations | Approval Requirement | Action on Rejection |
| :--- | :--- | :--- | :--- |
| **Low Risk** | Read files, generate unit tests, write documentation, internal code refactoring | Fully Autonomous (Auto-Approved) | N/A |
| **Medium Risk**| Modifying public API schemas, adding new external dependencies, committing code to feature branches | Asynchronous Review Queue (Notify & Timeout Auto-Approve) | Agent revises based on comments |
| **High Risk** | Production deployments, database schema migrations, modifying security/IAM rules, force-pushing git | Hard Gate (Requires explicit human signature) | Workflow halts; task aborted |

### 10.2 Interactive Review Queues
When a High Risk or failed evaluation gate occurs:
1. The Orchestrator pauses the task DAG node and transitions agent state to `WAITING_APPROVAL`.
2. A review ticket is published to the AegisOS Dashboard and Slack/Teams integration with complete context (diffs, test outputs, token costs, security analysis).
3. The human reviewer can:
   - **Approve**: Task resumes immediately.
   - **Reject with Comments**: Human provides natural language feedback; agent reads feedback, adjusts state, and retries.
   - **Direct Edit**: Human edits proposed code/spec directly; agent accepts modified state and proceeds.

---


# Document 14: AI AGENT ARCHITECTURE

## 1. Agent Lifecycle

### 1.1 Lifecycle State Transitions
Every AI Agent in AegisOS is an autonomous software worker operating through a defined 5-phase lifecycle: Creation, Initialization, Execution, Completion, and Termination.

```
+------------------+     +------------------+     +------------------+
|   1. CREATION    | --> | 2. INITIALIZATION| --> |   3. EXECUTION   |
| (Spawn Container/|     | (Fetch Context,  |     | (Reasoning Loop, |
|  Load Persona)   |     |  Mount Workspace)|     |  Tool Execution) |
+------------------+     +------------------+     +------------------+
                                                           |
                         +------------------+              v
                         |  5. TERMINATION  | <--- +------------------+
                         | (Unmount Storage,|      |  4. COMPLETION   |
                         |  Clean Resources)|      | (Validate Output,|
                         +------------------+      |  Write Memory)   |
                                                   +------------------+
```

### 1.2 Step-by-Step Execution Sequence
1. **Creation**: Orchestrator receives task from DAG queue. Spawns isolated execution container, assigns unique `agent_id`, loads agent role profile (e.g., Software Engineer).
2. **Initialization**: Mounts target repository filesystem volume. Fetches relevant project memory, task dependencies, system prompts, and tool bindings. Registers heartbeat with Redis.
3. **Execution**: Enters LLM reasoning loop (`ReAct` pattern: Reason -> Tool Invocation -> Observe Result -> Repeat). Logs every turn to PostgreSQL audit log.
4. **Completion**: Execution finishes. Output artifacts (code, specs, diffs) undergo automated validation checks (linting, tests, schema verification). Artifacts persisted to Project Memory.
5. **Termination**: Flushes metrics and token counts. Unmounts workspace volume, notifies event bus of completion (`aegis.events.<proj>.<role>.task_completed`), and releases process memory.

---

## 2. Agent State Machine

### 2.1 State Machine Specification
Agents operate as deterministic finite state machines. The system enforces strict transition validation rules.

```
                       +-------------------+
                       |       IDLE        |
                       +-------------------+
                                 |
                                 v (Task Assigned)
                       +-------------------+
                       |     ASSIGNED      |
                       +-------------------+
                                 |
                                 v (Context Loaded)
                       +-------------------+
           +---------> |      WORKING      | <---------+
           |           +-------------------+           |
           |                     |                     |
           |                     +-----------------+   |
           |                     |                 |   |
(Revision Requested)             v                 v   | (Retry on Recoverable Failure)
           |           +-------------------+  +-------------------+
           +---------- | WAITING_APPROVAL  |  |       ERROR       |
                       +-------------------+  +-------------------+
                                 |                     |
                                 v (Approved)          v (Max Retries Exceeded / Fatal)
                       +-------------------+  +-------------------+
                       |       DONE        |  |  TERMINATED / DLQ |
                       +-------------------+  +-------------------+
```

### 2.2 State Transition Matrix

| Current State | Target State | Trigger Condition | Guard Conditions | Actions Taken |
| :--- | :--- | :--- | :--- | :--- |
| `IDLE` | `ASSIGNED` | Task dispatched by Orchestrator | Task dependencies completed; worker memory available | Bind `task_id` to `agent_id`; update Redis state |
| `ASSIGNED` | `WORKING` | Workspace initialized | Volume mounted; environment variables loaded | Spin up heartbeat ping; enter reasoning loop |
| `WORKING` | `WAITING_APPROVAL`| High-risk tool triggered OR evaluation gate hit | Gate rules satisfied | Pause loop; publish review alert to event bus |
| `WAITING_APPROVAL`| `WORKING` | Human submits approval/feedback | Valid approval payload received | Inject human comments into prompt; resume loop |
| `WORKING` | `ERROR` | Unhandled exception / test failure / syntax error | Retry counter < Max Retries (3) | Log error; trigger self-correction backoff |
| `ERROR` | `WORKING` | Self-correction payload generated | Backoff timer elapsed | Re-inject error logs into prompt context |
| `WORKING` | `DONE` | Task execution complete & validation passed | All output validation tests pass | Commit workspace changes; write long-term memory |
| `ERROR` | `TERMINATED` | Unrecoverable error or max retries exceeded | Retry count >= 3 | Move task to DLQ; release system resources |

---

## 3. Agent Context Management

### 3.1 Context Scope Isolation
To ensure maximum reasoning accuracy and security, context is segmented into three strict tiers:
- **Task Scope**: Ephemeral memory relevant only to current sub-task (e.g., current error traceback, target file diff). Destroyed upon task completion.
- **Project Scope**: Shared context across all project agents (e.g., overall architectural rules, database schema, active API contracts).
- **Agent Scope**: Persistent persona constraints, accumulated learnings, and tool execution preferences for specific agent role.

### 3.2 Sliding Window & Token Management
Agents utilize an adaptive context window allocator optimized for 128k context windows:

```
+-------------------------------------------------------------------------------+
| System Prompt & Role Persona (15% / ~19,200 tokens)                           |
+-------------------------------------------------------------------------------+
| Project Architectural Rules & Memory (20% / ~25,600 tokens)                   |
+-------------------------------------------------------------------------------+
| Workspace Code Context & Active Diffs (35% / ~44,800 tokens)                   |
+-------------------------------------------------------------------------------+
| Dynamic Ephemeral Conversation History (20% / ~25,600 tokens) [Sliding Window]|
+-------------------------------------------------------------------------------+
| Reserved Generation Space (10% / ~12,800 tokens)                              |
+-------------------------------------------------------------------------------+
```

---

## 4. Agent Tool Interface

### 4.1 Tool Schema Specification
Agents interact with their workspace exclusively through strongly typed JSON-schema tool contracts.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AegisOSToolDefinition",
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "description": { "type": "string" },
    "parameters": {
      "type": "object",
      "properties": {
        "file_path": { "type": "string" },
        "content": { "type": "string" },
        "start_line": { "type": "integer" },
        "end_line": { "type": "integer" }
      },
      "required": ["file_path"]
    },
    "risk_level": { "type": "string", "enum": ["LOW", "MEDIUM", "HIGH"] }
  },
  "required": ["name", "description", "parameters", "risk_level"]
}
```

### 4.2 Standard Core AegisOS Tool Suite
1. `read_file(path, start_line, end_line)`: Reads workspace file contents within line bounds.
2. `write_file(path, content, create_dirs)`: Writes whole file contents safely.
3. `apply_patch(path, git_diff)`: Applies unified diff patches to code files.
4. `execute_bash(command, timeout_seconds)`: Runs shell commands in isolated container sandbox.
5. `git_operation(action, branch_name, commit_msg)`: Executes git commands (`commit`, `checkout`, `branch`, `push`).
6. `http_request(method, url, headers, body)`: Makes HTTP REST calls with egress domain filtering.
7. `query_database(connection_string, sql_query)`: Executes read-only or migration SQL scripts against DB.
8. `spawn_subagent(role, subtask_description)`: Delegates sub-tasks to child agents.

### 4.3 Tool Sandbox Security & Isolation
- **Container Sandboxing**: All tool executions (`execute_bash`, `write_file`) occur inside non-root Docker/gVisor sandbox containers.
- **Path Containment**: Workspace access is strictly jailed to `/workspace/<project_id>/`. Path traversal attempts (`../..`) are blocked at kernel/syscall layer.
- **Egress Network Rules**: Outbound internet traffic is blocked except to whitelisted API endpoints (OpenAI, Anthropic, internal package registries).

---

## 5. Agent Output Validation

### 5.1 Multi-Stage Validation Pipeline
Output generated by agents must pass a mandatory 4-stage automated gate before being accepted into the codebase:

```
+--------------------+     +--------------------+     +--------------------+     +--------------------+
|  1. Schema Check   | --> | 2. Static Parsing  | --> |  3. Automated      | --> | 4. Architectural   |
| (JSON / Tool Args) |     | (AST / Syntax /    |     |     Test Suite     |     |    Policy Rules    |
|                    |     |  Linting Verification)|  |   (Unit Tests)     |     | (Dependency Check) |
+--------------------+     +--------------------+     +--------------------+     +--------------------+
```

### 5.2 Self-Correction Loop
If validation fails at any stage:
1. The error details (e.g., AST parse error, pytest failure traceback, compiler error) are structured into an Error Payload.
2. The agent's loop is re-triggered with the Error Payload injected as a high-priority context message:
   `"Validation Failed at Stage 3 (Pytest). Error: Test test_user_authentication failed with AssertionError: Expected 200, got 401. Traceback: ... Please analyze and fix."`
3. The agent receives up to 3 self-correction iterations before triggering escalation.

---

## 6. Agent Collaboration Patterns

### 6.1 Hierarchical Delegation
Used for complex top-down features:
- **Product Owner** creates specification -> **Architect** creates technical design -> **Tech Lead** creates Task DAG -> **Software Engineers** implement components in parallel.

### 6.2 Peer Review & Feedback Loops
- Upon code completion by a **Software Engineer Agent**, a **Peer Review Agent** (or QA Agent) is spawned to conduct code review.
- The Reviewer agent generates a structured PR review containing inline suggestions.
- If changes are requested, the task returns to the Software Engineer Agent for iteration.

### 6.3 Escalation & Consensus Protocols
- If two agents reach a deadlock (e.g., QA agent rejects code implementation 3 times, while Engineer claims spec is ambiguous), the issue is automatically escalated to the **Tech Lead Agent** or **Orchestrator**.
- If unresolved after Tech Lead review, it triggers a High-Risk Human-in-the-Loop review event.

---

## 7. Agent Memory Integration

### 7.1 Ephemeral vs. Persistent Memory Integration
- **Short-Term Scratchpad**: High-speed in-memory state stored in Redis. Holds current intermediate reasoning steps, scratch math, and preliminary tool outputs.
- **Long-Term Memory**: Persistent store backed by PostgreSQL + pgvector. Holds completed task artifacts, ADRs, PR reviews, code embeddings, and past bug resolutions.

---

## 8. Agent Prompt Templates (All 6 MVP Agent Types)

### 8.1 Product Owner Agent System Prompt
```markdown
You are the AegisOS Product Owner Agent. Your role is to translate business concepts, user requirements, and raw requests into clear, comprehensive, and unambiguous Product Requirements Documents (PRDs) and User Stories.

RESPONSIBILITIES:
1. Analyze user requirements and business goals.
2. Define detailed functional requirements, non-functional requirements, and edge cases.
3. Decompose specifications into INVEST-compliant User Stories with explicit Acceptance Criteria (Given/When/Then format).
4. Identify risks, dependencies, and target user personas.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "prd_title": "string",
  "version": "1.0.0",
  "summary": "string",
  "target_personas": ["string"],
  "functional_requirements": [
    { "id": "FR-1", "title": "string", "description": "string", "priority": "HIGH|MEDIUM|LOW" }
  ],
  "user_stories": [
    {
      "story_id": "US-1",
      "title": "string",
      "as_a": "string",
      "i_want": "string",
      "so_that": "string",
      "acceptance_criteria": ["Given ... When ... Then ..."]
    }
  ]
}
```

### 8.2 Architect Agent System Prompt
```markdown
You are the AegisOS System Architect Agent. Your role is to transform PRDs and business specifications into robust, scalable, and secure technical architectures.

RESPONSIBILITIES:
1. Formulate end-to-end system designs, technical stacks, and data models.
2. Author formal Architectural Decision Records (ADRs) explaining trade-offs, rationale, and consequences.
3. Define component interaction diagrams, API schemas (OpenAPI), and database schemas.
4. Enforce enterprise security, compliance, performance, and scalability standards.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "architecture_title": "string",
  "overview": "string",
  "tech_stack": {
    "frontend": "string",
    "backend": "string",
    "database": "string",
    "cache": "string"
  },
  "adrs": [
    {
      "adr_id": "ADR-001",
      "title": "string",
      "status": "ACCEPTED",
      "context": "string",
      "decision": "string",
      "consequences": "string"
    }
  ],
  "api_specifications": "string (OpenAPI YAML/JSON format)",
  "database_schema_ddl": "string (SQL DDL format)"
}
```

### 8.3 Tech Lead Agent System Prompt
```markdown
You are the AegisOS Tech Lead Agent. Your role is to bridge technical architecture and engineering execution by creating actionable, dependency-mapped Task DAGs and guiding code generation.

RESPONSIBILITIES:
1. Decompose system architecture and PRDs into atomic engineering tasks.
2. Build Directed Acyclic Graphs (DAGs) defining exact execution order and dependency relationships.
3. Assign task complexity, estimated token budgets, and required agent capabilities.
4. Establish coding standards, project folder structures, and repository conventions.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "project_id": "string",
  "folder_structure": ["string"],
  "task_dag": [
    {
      "task_id": "TSK-001",
      "title": "string",
      "assigned_role": "SOFTWARE_ENGINEER",
      "dependencies": [],
      "required_capabilities": ["python", "postgres"],
      "token_budget": 50000,
      "instructions": "string"
    }
  ]
}
```

### 8.4 Software Engineer Agent System Prompt
```markdown
You are the AegisOS Software Engineer Agent. Your role is to write production-grade, highly efficient, well-tested code that strictly fulfills architectural specifications and user story acceptance criteria.

RESPONSIBILITIES:
1. Implement clean, modular, and idiomatic source code in designated languages.
2. Write unit tests accompanying code implementations (aiming for >85% code coverage).
3. Strictly follow project directory layouts, style guides, and linting rules.
4. Perform self-correction on syntax errors or failing test tracebacks.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "task_id": "string",
  "files_created_or_modified": [
    {
      "path": "string",
      "content": "string",
      "action": "CREATE|MODIFY|DELETE"
    }
  ],
  "unit_tests": [
    {
      "path": "string",
      "content": "string"
    }
  ],
  "implementation_notes": "string"
}
```

### 8.5 QA Engineer Agent System Prompt
```markdown
You are the AegisOS QA Engineer Agent. Your role is to guarantee software quality, correctness, and resilience through rigorous test creation, automated test execution, and bug regression testing.

RESPONSIBILITIES:
1. Analyze User Stories and Acceptance Criteria to write integration and E2E test suites.
2. Execute code in isolated test sandboxes and inspect test outputs and tracebacks.
3. File detailed, reproducible Bug Reports when test failures or edge-case defects occur.
4. Verify bug fixes generated by Software Engineer agents.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "test_execution_summary": {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "execution_time_sec": 0.0
  },
  "bug_reports": [
    {
      "bug_id": "BUG-001",
      "title": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "steps_to_reproduce": ["string"],
      "expected_behavior": "string",
      "actual_behavior": "string",
      "failed_test_name": "string"
    }
  ]
}
```

### 8.6 DevOps / Security Agent System Prompt
```markdown
You are the AegisOS DevOps & Security Agent. Your role is to manage CI/CD automation, Infrastructure as Code (IaC), containerization, dependency security scanning, and security policy compliance.

RESPONSIBILITIES:
1. Generate Dockerfiles, docker-compose configurations, and Kubernetes manifests.
2. Build CI/CD pipeline definitions (GitHub Actions, GitLab CI).
3. Conduct static application security testing (SAST) and secret leak detection.
4. Enforce least-privilege security controls and secure secret handling policies.

OUTPUT FORMAT:
You MUST structure your final output strictly in JSON according to the following schema:
{
  "devops_artifacts": [
    {
      "file_path": "string",
      "content": "string",
      "type": "DOCKERFILE|KUBERNETES|CICD|TERRAFORM"
    }
  ],
  "security_audit": {
    "vulnerabilities_found": 0,
    "findings": [
      {
        "severity": "HIGH|MEDIUM|LOW",
        "description": "string",
        "recommendation": "string"
      }
    ]
  }
}
```

---

## 9. Agent Retry and Error Handling

### 9.1 Exponential Backoff with Jitter Formula
To prevent retry thundering herds during system failures, retries utilize decorrelated jitter:
$$T_{	ext{wait}} = \min\left(T_{	ext{max}}, \; T_{	ext{base}} 	imes 2^{	ext{attempt}} + 	ext{random}(0, \; 	ext{jitter})ight)$$
Where $T_{	ext{base}} = 2.0	ext{s}$, $T_{	ext{max}} = 60.0	ext{s}$, and $	ext{jitter} = 1.5	ext{s}$.

### 9.2 Context-Aware Diagnostic Hierarchy
Errors are categorized to determine recovery path:
1. **Transient Network / API Error**: Instant exponential retry without context alteration.
2. **Syntax / Compilation Error**: Re-feed error traceback into prompt with request for self-correction.
3. **Missing Tool / Permission Denial**: Re-route task or update permissions; prompt agent with updated tool list.
4. **Logic / Test Assertion Failure**: Ingest test output diff, invoke QA context, and re-attempt generation up to 3 times.

---

## 10. Agent Audit Trail

### 10.1 Immutable Ledger Architecture
Every action taken by an agent is permanently recorded in an append-only PostgreSQL table `agent_audit_ledger`. This provides 100% auditability, compliance tracking, and deterministic workflow replaying.

```sql
CREATE TABLE agent_audit_ledger (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    project_id VARCHAR(64) NOT NULL,
    task_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    agent_role VARCHAR(64) NOT NULL,
    state_before VARCHAR(32) NOT NULL,
    state_after VARCHAR(32) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    raw_prompt TEXT NOT NULL,
    llm_response TEXT NOT NULL,
    tool_calls JSONB DEFAULT '[]'::jsonb,
    tool_results JSONB DEFAULT '[]'::jsonb,
    token_cost_usd NUMERIC(10, 6) DEFAULT 0.0,
    execution_time_ms INTEGER NOT NULL
);

CREATE INDEX idx_audit_project_task ON agent_audit_ledger(project_id, task_id);
CREATE INDEX idx_audit_agent ON agent_audit_ledger(agent_id);
```

---

## 11. Agent Budget Enforcement

### 11.1 Hard & Soft Constraint Boundaries
Each agent task execution runs under strict guardrails to prevent infinite execution loops or resource exhaustion:

| Guardrail Parameter | Soft Limit (Warning Alert) | Hard Limit (Kill Switch) | Action on Breach |
| :--- | :--- | :--- | :--- |
| **Max Tokens per Task** | 80,000 tokens | 120,000 tokens | Halts LLM call; triggers task summarization |
| **Max API Calls per Task**| 15 calls | 25 calls | Rejects further tool calls; forces final response |
| **Max Wall-Clock Time** | 10 minutes | 15 minutes | Sends `SIGTERM` to sandbox container; moves task to DLQ |
| **Max Financial USD Cost**| $2.50 USD | $5.00 USD | Revokes LLM API key authorization for session |

---


# Document 15: MEMORY ARCHITECTURE

## 1. Three-Tier Memory System Architecture

AegisOS employs a sophisticated Three-Tier Memory System designed to handle ephemeral working contexts, project-level persistence, and cross-project global organizational knowledge. This tri-tier division optimizes latency, cost, and recall fidelity across diverse agent activities.

```
+-------------------------------------------------------------------------------+
| Tier 1: AGENT MEMORY (Short-Term / Ephemeral)                                 |
| Scope: Single Task | Lifecycle: Task Duration | Store: Redis In-Memory            |
+-------------------------------------------------------------------------------+
                                        |
                                        v (Consolidation on Task Completion)
+-------------------------------------------------------------------------------+
| Tier 2: PROJECT MEMORY (Persistent / Project-Bound)                          |
| Scope: Single Project | Lifecycle: Project Lifetime | Store: Postgres + Vector    |
+-------------------------------------------------------------------------------+
                                        |
                                        v (Generalization & Distillation Pipeline)
+-------------------------------------------------------------------------------+
| Tier 3: GLOBAL MEMORY (Shared / Cross-Project)                                |
| Scope: Organization-wide | Lifecycle: Indefinite | Store: Central Vector Index    |
+-------------------------------------------------------------------------------+
```

### 1.1 Detailed Tier Specifications

#### Tier 1: Agent Memory (Short-Term Working Memory)
- **Scope & Boundary**: Isolated strictly to the active task execution bound to a specific `agent_id` and `task_id`.
- **Contents**: Current intermediate reasoning steps (`ReAct` thoughts), temporary scratchpad variables, raw unparsed tool execution results, recent code diff buffers, and pending sub-agent communication payloads.
- **Data Structures**: Stored in Redis using high-efficiency structures:
  - `aegis:mem:t1:{task_id}:stack` (Redis List for turn-by-turn execution history)
  - `aegis:mem:t1:{task_id}:scratchpad` (Redis Hash for scratchpad key-value variables)
  - `aegis:mem:t1:{task_id}:tokens` (Redis String for sliding-window token tracking)
- **Lifecycle & TTL**: Ephemeral. Assigned a strict Time-To-Live (TTL) of 24 hours. Garbage-collected automatically upon task transition to `DONE` or `TERMINATED`.

#### Tier 2: Project Memory (Persistent Project Knowledge)
- **Scope & Boundary**: Shared across all agents assigned to a specific `project_id`.
- **Contents**: Full repository source tree structure, Architectural Decision Records (ADRs), Product Requirements Documents (PRDs), database schemas, active OpenAPI specs, code review history, build logs, and unit test results.
- **Storage Engines**:
  - PostgreSQL (Relational schema for structured records: decisions, review outcomes, task DAG histories).
  - pgvector (Vector embeddings for semantic search across project code, docs, and diffs).
  - Content-Addressable Filesystem Storage (Git workspace repository, raw build outputs, and coverage reports).
- **Lifecycle**: Retained permanently for the active lifecycle of the project. Updated dynamically upon every task completion and git merge.

#### Tier 3: Global Memory (Cross-Project Organizational Knowledge)
- **Scope & Boundary**: Shared across all projects and agents in the entire organization / enterprise tenant.
- **Contents**: Reusable architectural design patterns, organization-wide coding style guides, corporate security compliance baselines, reusable library snippets, zero-day vulnerability signatures, and historical Root Cause Analysis (RCA) records from past incidents.
- **Storage Engines**: Centralized pgvector index / Chroma instance with multi-tenant workspace partitioning and strict Role-Based Access Control (RBAC).
- **Lifecycle**: Indefinite retention. Subject to continuous learning, semantic deduplication, and importance-score pruning.

---

### 1.2 Memory Tier Comparison Matrix

| Attribute | Tier 1: Agent Memory | Tier 2: Project Memory | Tier 3: Global Memory |
| :--- | :--- | :--- | :--- |
| **Primary Scope** | Single Agent Sub-Task | Single Project Workspace | Cross-Project / Enterprise Tenant |
| **Storage Engine** | Redis In-Memory Key-Value | PostgreSQL + pgvector + Filesystem | Central pgvector / Chroma Cluster |
| **Access Latency** | Sub-millisecond (<2ms) | Low latency (10ms - 50ms) | Fast semantic lookup (20ms - 80ms) |
| **Data Format** | MessagePack / JSON ephemeral strings | Relational tables, HNSW vector index, Git objects | Dense vector embeddings + Markdown docs |
| **Retention Period**| Active task duration (Max 24h TTL) | Lifetime of the project | Indefinite (Subject to decay pruning) |
| **Mutation Rate** | Extremely High (Multiple writes per sec) | Moderate (Writes on task completion) | Read-Heavy (Periodic async writes) |

---

## 2. Memory Storage Implementation

### 2.1 Structured Data Storage (PostgreSQL Schema DDL)
Structured project knowledge, engineering decisions, audit logs, and performance metrics are stored in a fully normalized PostgreSQL database. Below is the complete production DDL schema:

```sql
-- PostgreSQL DDL for AegisOS Memory Architecture

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Projects Entity
CREATE TABLE projects (
    project_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    repository_url VARCHAR(512),
    default_branch VARCHAR(64) DEFAULT 'main',
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Architectural Decision Records (ADR)
CREATE TABLE architectural_decision_records (
    adr_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PROPOSED', -- PROPOSED, ACCEPTED, REJECTED, SUPERSEDED
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    consequences TEXT NOT NULL,
    superseded_by VARCHAR(64) REFERENCES architectural_decision_records(adr_id),
    created_by_agent VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Technical Discussions & Architecture Notes
CREATE TABLE technical_discussions (
    discussion_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    participants JSONB NOT NULL, -- Array of agent roles e.g. ["ARCHITECT", "TECH_LEAD"]
    transcript TEXT NOT NULL,
    summary TEXT NOT NULL,
    action_items JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Code Reviews Log
CREATE TABLE code_reviews (
    review_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    task_id VARCHAR(64) NOT NULL,
    commit_hash VARCHAR(64) NOT NULL,
    reviewer_agent VARCHAR(64) NOT NULL,
    target_files JSONB NOT NULL,
    status VARCHAR(32) NOT NULL, -- PASSED, CHANGES_REQUESTED
    findings JSONB NOT NULL, -- Structured array of review comments & inline suggestions
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Security Reviews Log
CREATE TABLE security_reviews (
    sec_review_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    scanned_commit VARCHAR(64) NOT NULL,
    vulnerabilities_found INTEGER DEFAULT 0,
    findings_detail JSONB NOT NULL, -- SAST & secret scan findings
    passed_audit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Performance Benchmarks Log
CREATE TABLE performance_benchmarks (
    benchmark_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    commit_hash VARCHAR(64) NOT NULL,
    latency_p50_ms NUMERIC(10, 2),
    latency_p95_ms NUMERIC(10, 2),
    latency_p99_ms NUMERIC(10, 2),
    throughput_rps NUMERIC(10, 2),
    memory_peak_mb NUMERIC(10, 2),
    passed_threshold BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Bug Reports & Root Cause Analyses (RCAs)
CREATE TABLE bug_reports (
    bug_id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(project_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    severity VARCHAR(32) NOT NULL, -- CRITICAL, HIGH, MEDIUM, LOW
    repro_steps TEXT NOT NULL,
    root_cause TEXT,
    resolution_summary TEXT,
    associated_commit VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN', -- OPEN, IN_PROGRESS, RESOLVED, CLOSED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- Indexes for fast relational lookup
CREATE INDEX idx_adrs_project ON architectural_decision_records(project_id, status);
CREATE INDEX idx_reviews_task ON code_reviews(project_id, task_id);
CREATE INDEX idx_bugs_status ON bug_reports(project_id, status, severity);
```

---

### 2.2 Vector Embeddings Storage (pgvector Configuration)
Unstructured artifacts (source code chunks, AST documentation, ADR narratives, past bug post-mortems) are converted into dense vector embeddings using OpenAI `text-embedding-3-large` (1,536 dimensions) and indexed using pgvector.

```sql
-- Vector Embeddings Store Table
CREATE TABLE memory_vector_store (
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(64) NOT NULL,
    memory_tier VARCHAR(16) NOT NULL, -- 'PROJECT' or 'GLOBAL'
    entity_type VARCHAR(64) NOT NULL, -- 'CODE', 'ADR', 'DISCUSSION', 'BUG_RCA', 'SECURITY'
    entity_id VARCHAR(64) NOT NULL,
    content_chunk TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Hierarchical Navigable Small World (HNSW) Index Configuration
-- Configured with Cosine Distance operator for high-accuracy similarity search
CREATE INDEX idx_vector_store_hnsw ON memory_vector_store 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Metadata index for pre-filtering queries by project, tier, and entity type
CREATE INDEX idx_vector_metadata ON memory_vector_store USING gin (metadata);
CREATE INDEX idx_vector_project_entity ON memory_vector_store (project_id, entity_type);
```

#### Vector Tuning Parameters
- **Dimensions**: 1,536 dimensions (`text-embedding-3-large`).
- **Distance Metric**: Cosine Distance ($1 - 	ext{cosine\_similarity}$).
- **HNSW Parameters**:
  - `m = 16`: Number of bi-directional links created per vector node.
  - `ef_construction = 64`: Search depth during index construction. Balances build speed and recall.
  - `ef_search = 40`: Query-time search capacity trade-off for sub-30ms similarity recall.

---

### 2.3 File Artifact Storage Hierarchy
Source files, binary build outputs, test execution artifacts, and git objects are organized in a content-addressable storage structure:

```
/app/storage/
├── projects/
│   └── <project_id>/
│       ├── workspace/                 # Active Git clone repository directory
│       │   ├── .git/
│       │   └── src/
│       ├── artifacts/                 # Task execution artifacts
│       │   ├── builds/                # Compiled binaries, tarballs, wheels
│       │   ├── test_reports/          # Pytest XML / HTML test outputs
│       │   └── coverage/              # Code coverage matrices
│       ├── diffs/                     # Saved git patch diffs per task ID
│       └── logs/                      # Raw console stdout/stderr logs per agent run
└── global/
    ├── pattern_templates/            # Shared architectural scaffolding
    └── security_rules/                # Enterprise SAST rulesets
```

---

## 3. Memory Retrieval System

### 3.1 Semantic Search Engine (Dense Vector RAG)
Agents perform semantic searches across Project and Global memory to discover relevant context prior to executing complex code edits or architectural planning.

```python
import psycopg2
from typing import List, Dict, Any

async def query_semantic_memory(
    db_conn,
    project_id: str,
    query_embedding: List[float],
    entity_type: str = "CODE",
    top_k: int = 5,
    similarity_threshold: float = 0.75
) -> List[Dict[str, Any]]:
    """
    Executes dense vector similarity search with metadata pre-filtering using pgvector HNSW index.
    """
    sql = """
        SELECT vector_id, entity_id, content_chunk, metadata,
               1 - (embedding <=> %s::vector) AS similarity
        FROM memory_vector_store
        WHERE project_id = %s
          AND entity_type = %s
          AND (1 - (embedding <=> %s::vector)) >= %s
        ORDER BY embedding <=> %s::vector ASC
        LIMIT %s;
    """
    cursor = db_conn.cursor()
    cursor.execute(
        sql,
        (query_embedding, project_id, entity_type, query_embedding, similarity_threshold, query_embedding, top_k)
    )
    results = cursor.fetchall()
    return [
        {
            "vector_id": r[0],
            "entity_id": r[1],
            "content": r[2],
            "metadata": r[3],
            "similarity": float(r[4])
        }
        for r in results
    ]
```

---

### 3.2 Temporal Search Engine (Point-in-Time State Reconstruction)
The Temporal Search Engine reconstructs the exact state of project knowledge, active ADRs, and codebase structure at any given point in past time:
- Uses SQL temporal queries against `created_at` timestamps combined with Git commit trees (`git checkout <commit_sha_at_timestamp>`).
- Reconstructs API schemas and architectural constraints active when a specific bug was reported, allowing agents to debug regressions in historical context.

---

### 3.3 Causal Search Engine (DAG Lineage Tracing)
The Causal Search Engine traces cause-and-effect chains connecting business requirements down to execution artifacts and defects. It uses PostgreSQL Recursive Common Table Expressions (CTEs) across `agent_audit_ledger` and `bug_reports` to trace lineage:

```
[Product Story: FR-1] ---> [ADR-002: Postgres Migration] ---> [Task: TSK-014]
                                                                     |
                                                                     v
[Bug Report: BUG-008] <--- [Failed Pytest] <--- [Code Commit: a8f91c]
```

```sql
-- Recursive CTE for Causal Lineage Tracing
WITH RECURSIVE causal_lineage AS (
    -- Anchor member: Target bug report or task
    SELECT audit_id, task_id, correlation_id, agent_role, tool_calls, timestamp
    FROM agent_audit_ledger
    WHERE task_id = 'TSK-014'
    
    UNION ALL
    
    -- Recursive member: Join parent execution steps sharing correlation_id
    SELECT a.audit_id, a.task_id, a.correlation_id, a.agent_role, a.tool_calls, a.timestamp
    FROM agent_audit_ledger a
    INNER JOIN causal_lineage c ON a.correlation_id = c.correlation_id
    WHERE a.timestamp < c.timestamp
)
SELECT * FROM causal_lineage ORDER BY timestamp ASC;
```

---

### 3.4 Hybrid Search & Reciprocal Rank Fusion (RRF)
To combine keyword accuracy (BM25) with conceptual vector similarity, AegisOS implements **Reciprocal Rank Fusion (RRF)**:

```python
def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combines dense vector ranks and sparse BM25 ranks using RRF.
    RRF_Score(d) = sum(1 / (k + rank_m(d)))
    """
    scores = {}
    doc_map = {}

    for rank, doc in enumerate(dense_results):
        doc_id = doc["entity_id"]
        doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + (rank + 1)))

    for rank, doc in enumerate(sparse_results):
        doc_id = doc["entity_id"]
        doc_map[doc_id] = doc
        scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + (rank + 1)))

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        {**doc_map[doc_id], "rrf_score": score}
        for doc_id, score in sorted_docs
    ]
```

---

## 4. Memory Consolidation

### 4.1 Ephemeral to Persistent Consolidation Pipeline
Upon task completion, intermediate agent execution logs and scratchpad variables are distilled into long-term Project Memory through an automated pipeline:

```
+-------------------------------------------------------------------------------+
| Step 1: Task Completion Event Triggered on Event Bus                          |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Step 2: Ingest Ephemeral Redis Scratchpad & Raw Execution Audit Logs         |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Step 3: Summarizer Sub-Agent Extracts Key Decisions, Diffs & Bug Fixes       |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Step 4: Generate Vector Embeddings (text-embedding-3-large)                   |
+-------------------------------------------------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
| Step 5: ACID Insert into PostgreSQL Tables + pgvector Store                   |
+-------------------------------------------------------------------------------+
```

---

## 5. Memory Pruning & Lifecycle Management

### 5.1 Retention & Eviction Policies

1. **Tier 1 (Agent Ephemeral Memory)**:
   - Redis TTL mechanism auto-purges keys after 24 hours.
   - Immediate manual flush triggered when task reaches status `DONE`.
2. **Tier 2 (Project Memory)**:
   - Persistent for project lifetime.
   - Code chunk vectors are invalidated and re-embedded whenever `git diff` shows modifications to the underlying source file.
3. **Tier 3 (Global Memory)**:
   - Evaluated bi-weekly using an **Importance Score Decay Function**:
     $$	ext{Importance Score} = 	ext{AccessCount} 	imes e^{-\lambda (	ext{CurrentTime} - 	ext{LastAccessed})}$$
     Where $\lambda = 0.05$. If Importance Score drops below $0.10$, the memory chunk is archived to Amazon S3 cold storage.

---

## 6. Memory Sharing & Synchronization

### 6.1 Role-Based Access Control (RBAC) Matrix

| Agent Role | Tier 1 Access | Tier 2 (Project) Access | Tier 3 (Global) Access |
| :--- | :--- | :--- | :--- |
| **Product Owner** | Read/Write Own | Read All, Write PRDs/Stories | Read Only |
| **Architect** | Read/Write Own | Read All, Write ADRs/Schemas | Read/Write Templates |
| **Tech Lead** | Read/Write Own | Read All, Write Task DAGs | Read Only |
| **Software Engineer** | Read/Write Own | Read All, Write Code/Tests | Read Only |
| **QA Engineer** | Read/Write Own | Read All, Write Bugs/Test Logs | Read Only |
| **DevOps / Security** | Read/Write Own | Read All, Write Pipelines/Audit | Read/Write Security Rules |

### 6.2 Real-Time Memory Cache Synchronization
When an agent creates or updates a Tier 2 memory entity (e.g., Architect publishes new ADR), an invalidation event is broadcast across Redis Pub/Sub:
- Channel: `aegis.memory.invalidation.<project_id>`
- Payload: `{"event": "MEMORY_UPDATED", "entity_type": "ADR", "entity_id": "ADR-005"}`
- Listening active agent containers purge local in-memory context caches and pull updated entity state from PostgreSQL.

---

## 7. Memory Versioning & Lineage

### 7.1 Branch-Aware Vector Namespaces
Memory state forks parallel to repository Git branches:
- When an agent checks out a branch (`feature/user-auth`), vector embeddings produced on that branch receive metadata tag `{"branch": "feature/user-auth"}`.
- Vector search queries on feature branches execute fallback queries: Search `feature/user-auth` namespace first; if result count < top_k, fall back to `main` branch vector space.
- Merging a Git PR triggers an automated vector namespace merge script.

---

## 8. Permanent Engineering Memory Subsystem

The Permanent Engineering Memory Subsystem forms the organizational single source of truth for engineering knowledge across six specialized repositories:

### 8.1 Architectural Decision Records (ADR Repository)
Stores all formal architectural decisions formatted in Nygard structure. Stored in `architectural_decision_records` table and indexed in pgvector.

### 8.2 Technical Discussions & Design Notes
Preserves raw transcripts and distilled summaries of multi-agent architecture discussions, recording key trade-offs considered and rationale.

### 8.3 Code Review History & Antipattern Catalog
Maintains historical PR reviews to identify recurring code smells or anti-patterns across projects (e.g., detecting repeated SQL injection risks or unhandled promise rejections).

### 8.4 Security Review & Vulnerability Store
Maintains threat models, SAST scan results, dependency CVE audits, and historical security patch resolutions.

### 8.5 Performance Benchmark History
Tracks execution time (p95 latency), throughput (RPS), and memory consumption metrics across commit histories to detect performance regressions.

### 8.6 Bug Reports & Root Cause Analyses (RCA Ledger)
Maintains post-mortems for software defects. When a new bug is detected, QA agents query the RCA Ledger to determine if similar bugs were previously solved in other components.

---

