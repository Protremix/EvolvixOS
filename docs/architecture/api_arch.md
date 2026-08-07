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

## 13.3 REQUEST & RESPONSE FORMAT (JSON SCHEMAS)

All API exchanges enforce strict JSON schemas validated via Pydantic v2.

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

### 13.3.2 Standard Paginated Collection Response Schema
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

API endpoints support uniform query parameter operators for filtering and sorting collections.

### 13.5.1 Query Parameters Syntax
- **Filtering:** Field names accept square brackets for evaluation operators:
  - `GET /api/v1/agents?filter[status]=executing`
  - `GET /api/v1/agents?filter[created_at][gte]=2026-08-01T00:00:00Z`
  - `GET /api/v1/projects?filter[language]=python,typescript` (IN operator)
- **Sorting:** Multi-field sorting controlled via `sort` parameter (comma-separated, `-` prefix for descending order):
  - `GET /api/v1/projects?sort=-updated_at,name`

---

## 13.6 RATE LIMITING STRATEGY

AegisOS employs a dual-tier rate limiting mechanism backed by Redis sliding window algorithms.

```
Request Received
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 1: Per-IP / Per-User Token Bucket                   │ (Global 120 req/min)
└─────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│ Tier 2: Per-Endpoint High-Cost Limit                    │ (e.g. /agents/{id}/execute - 10 req/min)
└─────────────────────────────────────────────────────────┘
       │
       ▼
Process Request or Return HTTP 429
```

### 13.6.1 Standard Rate Limit Headers
All API responses include standard rate limit metadata headers:
- `X-RateLimit-Limit`: Maximum requests permitted within the time window.
- `X-RateLimit-Remaining`: Remaining request quota in current window.
- `X-RateLimit-Reset`: Unix timestamp when current quota resets.
- `Retry-After`: Returned on HTTP `429 Too Many Requests` specifying seconds to wait.

---

## 13.7 API KEY MANAGEMENT

System API Keys enable programatic machine-to-machine integrations (e.g., CI/CD pipelines, custom CLI tooling).

### 13.7.1 Key Lifecycle & Security Rules
1. **Key Format:** `aegis_live_[32_random_alphanumeric_chars]` or `aegis_test_[32_chars]`.
2. **Hash-Only Storage:** Plaintext API keys are displayed **once upon generation** and never stored in plain text. PostgreSQL stores only the **SHA-256 cryptographic hash** of the key.
3. **Scoping:** Every key is bound to explicit IAM permission scopes (e.g., `["agent:execute", "repo:read"]`).
4. **Revocation:** Instantaneous cache invalidation in Redis (`DEL apikey:{hash}`).

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

## 13.9 WEBHOOK DESIGN & INTEGRATION

External services can subscribe to outbound webhook notifications for asynchronous system events.

### 13.9.1 Signature Verification (`X-Aegis-Signature`)
Every webhook request contains an HMAC-SHA256 signature header computed using the shared secret:

```python
# Signature Generation Reference Logic
import hmac
import hashlib

def generate_webhook_signature(payload_bytes: bytes, secret: str) -> str:
    signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"
```

---

## 13.10 API VERSIONING & EVOLUTION STRATEGY

1. **URL-Path Versioning (Primary):** Primary API versions are embedded directly in the URI path (`/api/v1/`, `/api/v2/`).
2. **Deprecation Sunset Policy:** When an API endpoint or version is marked for deprecation:
   - Responses include RFC standard headers:
     - `Deprecation: @1785888000` (Unix timestamp)
     - `Sunset: Wed, 05 Aug 2027 00:00:00 GMT`
     - `Link: <https://aegisos.dev/docs/migration-v2>; rel="successor-version"`
   - Minimum **12-month migration window** provided prior to endpoint removal.

---

## 13.11 OPENAPI SPECIFICATION & SDK GENERATION

FastAPI automatically synthesizes the OpenAPI 3.1 schema. Client SDKs for TypeScript, Python, and Go are generated using `openapi-generator-cli` and `Fern` in CI/CD pipelines:

```bash
# Automated SDK Generation Build Step
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

