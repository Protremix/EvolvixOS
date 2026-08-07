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
