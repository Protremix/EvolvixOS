# VERDIS GOVERNANCE DOCUMENT 05: API STANDARDS

**Document ID:** VERDIS-GOV-05  
**Title:** Verdis Ecosystem Universal API Interface & Protocol Standards  
**Version:** 1.0.0  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT GOVERNANCE DOCUMENT  
**Applies To:** All Software Engineers, AI Agents, Sub-agents, API Architects, and Integration Developers in the Verdis Ecosystem.

---

## TABLE OF CONTENTS
1. [Unified API Design Charter](#1-unified-api-design-charter)
   1.1 [Ecosystem API Architecture Overview](#11-ecosystem-api-architecture-overview)
   1.2 [Core Integration Principles](#12-core-integration-principles)
   1.3 [Protocol Selection Decision Tree](#13-protocol-selection-decision-tree)
   1.4 [Cross-Protocol Compatibility & Serialization](#14-cross-protocol-compatibility--serialization)
2. [JSON-RPC 2.0 Specifications (Verdis Substrate Node)](#2-json-rpc-20-specifications-verdis-substrate-node)
   2.1 [RPC Transport & Network Endpoints](#21-rpc-transport--network-endpoints)
   2.2 [Substrate Method Naming Conventions](#22-substrate-method-naming-conventions)
   2.3 [Standard Request & Response Payloads](#23-standard-request--response-payloads)
   2.4 [JSON-RPC Standard Error Codes Table](#24-json-rpc-standard-error-codes-table)
   2.5 [Substrate Custom RPC Implementation Code](#25-substrate-custom-rpc-implementation-code)
   2.6 [WebSocket RPC Subscription Lifecycle](#26-websocket-rpc-subscription-lifecycle)
3. [REST API Standards (AegisOS Backend)](#3-rest-api-standards-aegisos-backend)
   3.1 [URI Hierarchy & Versioning (`/api/v1/`)](#31-uri-hierarchy--versioning-apiv1)
   3.2 [HTTP Verbs & Method Semantics](#32-http-verbs--method-semantics)
   3.3 [Standard Response Envelopes & HTTP Status Codes](#33-standard-response-envelopes--http-status-codes)
   3.4 [Pagination, Sorting & Filtering Specifications](#34-pagination-sorting--filtering-specifications)
   3.5 [FastAPI REST Router & Pydantic Schema Example](#35-fastapi-rest-router--pydantic-schema-example)
   3.6 [SDK Client Generation Pattern (Python & TypeScript)](#36-sdk-client-generation-pattern-python--typescript)
4. [WebSocket Event Streaming Standards](#4-websocket-event-streaming-standards)
   4.1 [Connection Handshake & Authentication](#41-connection-handshake--authentication)
   4.2 [WebSocket Event Envelope Schema](#42-websocket-event-envelope-schema)
   4.3 [Subscription & Channel Management Model](#43-subscription--channel-management-model)
   4.4 [Heartbeat Ping/Pong Protocol](#44-heartbeat-pingpong-protocol)
5. [gRPC Specifications (Internal Microservices)](#5-grpc-specifications-internal-microservices)
   5.1 [Protocol Buffers (proto3) Naming Conventions](#51-protocol-buffers-proto3-naming-conventions)
   5.2 [Service Definition Standards](#52-service-definition-standards)
   5.3 [gRPC Status Code Mapping](#53-grpc-status-code-mapping)
   5.4 [Exhaustive Protobuf Definition (`.proto`)](#54-exhaustive-protobuf-definition-proto)
6. [Authentication, Authorization & Rate Limiting](#6-authentication-authorization--rate-limiting)
   6.1 [Bearer Token Authentication Flow](#61-bearer-token-authentication-flow)
   6.2 [Rate Limiting Specifications (100 req/min Default)](#62-rate-limiting-specifications-100-reqmin-default)
   6.3 [Rate Limiting Response Headers](#63-rate-limiting-response-headers)
7. [API Documentation Requirements](#7-api-documentation-requirements)
   7.1 [Mandatory OpenAPI 3.1 Specification](#71-mandatory-openapi-31-specification)
   7.2 [AsyncAPI Specification for WebSockets/SSE](#72-asyncapi-specification-for-websocketssse)
   7.3 [Complete OpenAPI 3.1 YAML Example](#73-complete-openapi-31-yaml-example)
8. [API Design & Compliance Checklists](#8-api-design--compliance-checklists)
   8.1 [REST API Compliance Checklist](#81-rest-api-compliance-checklist)
   8.2 [JSON-RPC & WebSocket Compliance Checklist](#82-json-rpc--websocket-compliance-checklist)

---

## 1. UNIFIED API DESIGN CHARTER

### 1.1 Ecosystem API Architecture Overview
The Verdis Ecosystem exposes four primary API protocol layers across its 7 products:
- **JSON-RPC 2.0:** Blockchain state queries, extrinsic submissions, and node status (Port 9944).
- **REST (HTTP/2):** AegisOS task management, user administration, and system orchestration (Port 8000).
- **WebSocket & SSE:** Real-time block execution feeds, AI CTO pipeline progress streaming.
- **gRPC:** High-throughput, low-latency internal communication between AegisOS worker agents and chain indexers (Port 50051).

```
 +-------------------------------------------------------------------------+
 |                      UNIFIED API INTERFACE MATRIX                       |
 +-------------------------------------------------------------------------+
 | Protocol  | Target Component     | Primary Endpoint URL                 |
 | --------- | -------------------- | ------------------------------------ |
 | JSON-RPC  | Verdis Chain Node    | `ws://91.98.160.145:9944`            |
 | REST API  | AegisOS Backend      | `https://verdis.network/api/v1`      |
 | SSE Stream| Live Event Pipeline  | `https://verdis.network/api/v1/stream`|
 | gRPC      | Internal Indexer     | `127.0.0.1:50051` (Host Internal)     |
 +-------------------------------------------------------------------------+
```

### 1.2 Core Integration Principles
1. **Strict Versioning:** All external REST APIs must include an explicit major version prefix (`/api/v1/`). Breaking changes require a new version path (`/api/v2/`).
2. **Schema First:** Every API endpoint must be declared using an explicit schema (OpenAPI 3.1, Protobuf v3, or JSON Schema) before code implementation begins.
3. **Idempotency:** Non-mutating methods (`GET`, `HEAD`) must be side-effect free. `PUT` and `DELETE` requests must be idempotent.

### 1.3 Protocol Selection Decision Tree
- Use **JSON-RPC** for querying blockchain ledger state, reading SS58 accounts, or broadcasting signed extrinsics.
- Use **REST** for standard CRUD operations on AegisOS tasks, user accounts, and marketplace items.
- Use **SSE / WebSockets** for streaming live execution logs, CTO pipeline transitions, or block headers.
- Use **gRPC** for high-throughput, binary-serialized inter-container communications.

### 1.4 Cross-Protocol Compatibility & Serialization
To guarantee interoperability across languages (Rust, Python, TypeScript, Go):
- All 64-bit integers (`u64`, `i64`, `u128`, `Balance`) in JSON payloads MUST be serialized as hex strings or decimal strings to prevent JavaScript IEEE 754 precision loss.
- Timestamps must always follow ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`).
- Cryptographic hashes (block hashes, transaction hashes) must be 0x-prefixed hex strings.

---

## 2. JSON-RPC 2.0 SPECIFICATIONS (VERDIS SUBSTRATE NODE)

### 2.1 RPC Transport & Network Endpoints
The Verdis Substrate node exposes JSON-RPC 2.0 over WebSocket and HTTP interfaces:
- **Primary Endpoint:** `ws://91.98.160.145:9944` (or `https://verdis.network/rpc` via Nginx)
- **Protocol:** JSON-RPC 2.0 Specification (RFC 4627)

### 2.2 Substrate Method Naming Conventions
Method names follow the `namespace_methodName` pattern:
- **System Namespace:** `system_name`, `system_version`, `system_health`
- **Chain Namespace:** `chain_getBlock`, `chain_getBlockHash`, `chain_getFinalizedHead`
- **State Namespace:** `state_getStorage`, `state_getRuntimeVersion`
- **Author Namespace:** `author_submitExtrinsic`, `author_submitAndWatchExtrinsic`
- **Verdis Custom Namespace:** `verdis_getValidatorSet`, `verdis_getDPoSMetrics`

### 2.3 Standard Request & Response Payloads

#### Request Payload Example:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "verdis_getValidatorSet",
  "params": []
}
```

#### Successful Response Payload Example:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "active_validators": [
      "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
      "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"
    ],
    "total_staked_vrdx": "14000000000000000000000",
    "active_era": 42
  }
}
```

### 2.4 JSON-RPC Standard Error Codes Table

| Error Code | Error Message | Meaning / Trigger Condition |
| :--- | :--- | :--- |
| **`-32700`** | `Parse error` | Invalid JSON received by the RPC server. |
| **`-32600`** | `Invalid Request` | The JSON sent is not a valid Request object. |
| **`-32601`** | `Method not found` | The requested RPC method does not exist on the node. |
| **`-32602`** | `Invalid params` | Method parameters are invalid or out of expected range. |
| **`-32603`** | `Internal error` | Internal Substrate runtime execution error. |
| **`-32000`** | `Extrinsic failed` | Transaction validation or pool check failed. |
| **`-32001`** | `Block not found` | Requested block hash or height does not exist on-chain. |

### 2.5 Substrate Custom RPC Implementation Code

```rust
// blockchain/node/src/rpc.rs
use std::sync::Arc;
use jsonrpsee::{core::RpcResult, proc_macros::rpc};
use sp_api::ProvideRuntimeApi;
use sp_blockchain::HeaderBackend;
use sp_runtime::traits::Block as BlockT;

#[rpc(server)]
pub trait VerdisApi<BlockHash> {
    #[method(name = "verdis_getDPoSMetrics")]
    fn get_dpos_metrics(&self, at: Option<BlockHash>) -> RpcResult<DPoSMetrics>;
}

pub struct VerdisRpcStruct<C, B> {
    client: Arc<C>,
    _marker: std::marker::PhantomData<B>,
}

impl<C, B> VerdisApiServer<<B as BlockT>::Hash> for VerdisRpcStruct<C, B>
where
    B: BlockT,
    C: ProvideRuntimeApi<B> + HeaderBackend<B> + 'static,
{
    fn get_dpos_metrics(&self, _at: Option<<B as BlockT>::Hash>) -> RpcResult<DPoSMetrics> {
        Ok(DPoSMetrics {
            active_validator_count: 14,
            total_supply_vrdx: "100000000000000000000000000000".to_string(),
            dpos_era: 42,
        })
    }
}
```

### 2.6 WebSocket RPC Subscription Lifecycle
Clients subscribe to live block headers via WebSocket RPC:
1. Client sends `chain_subscribeNewHeads`.
2. Server responds with subscription ID `"sub_89124a1"`.
3. Server streams `chain_newHead` notifications for each finalized block.
4. Client unsubscribes using `chain_unsubscribeNewHeads` with subscription ID.

---

## 3. REST API STANDARDS (AEGISOS BACKEND)

```
 +-------------------------------------------------------------------------+
 |                     AEGISOS REST API SPECIFICATION                      |
 +-------------------------------------------------------------------------+
 | Base URL        | `https://verdis.network/api/v1`                       |
 | Payload Format  | JSON (`Content-Type: application/json`)               |
 | Auth Header     | `Authorization: Bearer <JWT_ACCESS_TOKEN>`            |
 | Rate Limit      | 100 requests / minute per client                      |
 +-------------------------------------------------------------------------+
```

### 3.1 URI Hierarchy & Versioning (`/api/v1/`)
URI resource paths must use plural nouns, lowercase characters, and hyphen-separated word boundaries:
- `GET /api/v1/tasks` — List all engineering tasks.
- `POST /api/v1/tasks` — Create a new task.
- `GET /api/v1/tasks/{task_id}` — Retrieve a specific task by ID.
- `GET /api/v1/tasks/{task_id}/logs` — Retrieve logs for a specific task.

### 3.2 HTTP Verbs & Method Semantics
- **`GET`:** Safe read operations. Must never mutate server state.
- **`POST`:** Resource creation or launching execution pipelines.
- **`PUT`:** Full replacement of a resource representation.
- **`PATCH`:** Partial update of specific resource attributes.
- **`DELETE`:** Resource removal.

### 3.3 Standard Response Envelopes & HTTP Status Codes

#### Standard Success Response (HTTP 200 / 201):
```json
{
  "success": true,
  "data": {
    "task_id": "task_98124a1",
    "title": "Implement Pallet Assets",
    "status": "COMPLETED",
    "pipeline_step": 9
  },
  "timestamp_utc": "2026-08-05T09:28:14Z"
}
```

#### Standard Error Response (HTTP 4xx / 5xx):
```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task ID task_99999 does not exist in AegisOS database",
    "details": []
  },
  "timestamp_utc": "2026-08-05T09:28:14Z"
}
```

#### HTTP Status Codes Matrix:

| HTTP Status Code | Meaning | Usage in Verdis Ecosystem |
| :--- | :--- | :--- |
| **`200 OK`** | Success | Standard successful `GET`, `PUT`, or `PATCH` request. |
| **`201 Created`** | Created | Successful resource creation via `POST`. |
| **`204 No Content`** | Deleted | Successful `DELETE` operation returning empty body. |
| **`400 Bad Request`** | Validation Error | Payload malformed or Pydantic validation failed. |
| **`401 Unauthorized`** | Auth Missing | Invalid, expired, or missing JWT Bearer token. |
| **`403 Forbidden`** | Permission Denied | Authenticated user lacks required RBAC role. |
| **`404 Not Found`** | Not Found | Requested resource URI does not exist. |
| **`409 Conflict`** | Conflict | Unique constraint violation (e.g. duplicate user email). |
| **`422 Unprocessable`** | Semantic Error | Syntactically valid JSON with unprocessable business values. |
| **`429 Too Many Requests`**| Rate Limited | Exceeded rate limit threshold (100 req/min). |
| **`500 Internal Error`** | Server Fault | Unhandled Python/AegisOS backend exception. |

### 3.4 Pagination, Sorting & Filtering Specifications
Collections queries support standard query parameters:
- **Pagination:** Query parameters `page` (default `1`) and `limit` (default `20`, max `100`).
  - Example: `GET /api/v1/tasks?page=2&limit=50`
- **Sorting:** Query parameter `sort` with `-` prefix for descending order.
  - Example: `GET /api/v1/tasks?sort=-created_at`
- **Filtering:** Explicit query parameters matching schema fields.
  - Example: `GET /api/v1/tasks?status=IN_PROGRESS&component=blockchain`

### 3.5 FastAPI REST Router & Pydantic Schema Example

```python
# aegisos/app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Engineering Tasks"])

class TaskResponse(BaseModel):
    task_id: str
    title: str
    status: str
    pipeline_step: int
    created_at: datetime

class PaginatedTasksResponse(BaseModel):
    items: List[TaskResponse]
    total_count: int
    page: int
    limit: int

@router.get("", response_model=PaginatedTasksResponse)
async def list_engineering_tasks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status")
) -> PaginatedTasksResponse:
    # Returns a paginated list of engineering tasks executing in the CTO Pipeline.
    return PaginatedTasksResponse(
        items=[],
        total_count=0,
        page=page,
        limit=limit
    )
```

### 3.6 SDK Client Generation Pattern (Python & TypeScript)
SDKs wrapper libraries in `Product 7` must be automatically generated from the OpenAPI spec:

```typescript
// frontend/src/services/apiClient.ts
export class VerdisApiClient {
  private baseUrl: string;
  private token: string | null;

  constructor(baseUrl = 'https://verdis.network/api/v1', token: string | null = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async getTasks(page = 1, limit = 20): Promise<PaginatedTasksResponse> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    const res = await fetch(`${this.baseUrl}/tasks?page=${page}&limit=${limit}`, { headers });
    if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
    return res.json();
  }
}
```

---

## 4. WEBSOCKET EVENT STREAMING STANDARDS

### 4.1 Connection Handshake & Authentication
WebSockets are used for bidirectional streaming between clients and AegisOS:
- **Endpoint:** `wss://verdis.network/api/v1/ws`
- **Handshake Auth:** Pass JWT token in query parameter `?token=<JWT_TOKEN>` or initial connection frame.

### 4.2 WebSocket Event Envelope Schema

```json
{
  "event_type": "CTO_PIPELINE_STEP_UPDATE",
  "channel": "tasks:task_98124a1",
  "timestamp_utc": "2026-08-05T09:28:14Z",
  "payload": {
    "task_id": "task_98124a1",
    "previous_step": 4,
    "current_step": 5,
    "step_name": "AUTOMATED_TESTING",
    "status": "IN_PROGRESS"
  }
}
```

### 4.3 Subscription & Channel Management Model
Clients subscribe to channels by sending JSON action frames:
```json
{
  "action": "SUBSCRIBE",
  "channels": ["chain:blocks", "tasks:task_98124a1"]
}
```

### 4.4 Heartbeat Ping/Pong Protocol
To prevent stale TCP connection accumulation, the WebSocket server dispatches a `PING` frame every **30 seconds**. Clients must respond with a `PONG` frame within **5 seconds**, or the connection will be terminated.

---

## 5. GRPC SPECIFICATIONS (INTERNAL MICROSERVICES)

### 5.1 Protocol Buffers (proto3) Naming Conventions
- **Proto Files:** Lowercase `snake_case.proto` (e.g., `cto_service.proto`).
- **Services:** `PascalCase` ending in `Service` (e.g., `TaskOrchestratorService`).
- **RPC Methods:** `PascalCase` verb-noun phrases (e.g., `ExecutePipelineStep`).
- **Messages:** `PascalCase` nouns (e.g., `PipelineStepRequest`).
- **Fields:** Lowercase `snake_case` (e.g., `task_id`, `step_number`).

### 5.2 Service Definition Standards
All internal gRPC services must support structured error status objects (`google.rpc.Status`).

### 5.3 gRPC Status Code Mapping

| gRPC Status Code | HTTP Equivalent | Trigger Condition |
| :--- | :--- | :--- |
| **`OK` (0)** | 200 OK | Operation completed successfully. |
| **`INVALID_ARGUMENT` (3)** | 400 Bad Request | Client specified an invalid argument payload. |
| **`UNAUTHENTICATED` (16)**| 401 Unauthorized | Missing or invalid authentication metadata. |
| **`PERMISSION_DENIED` (7)**| 403 Forbidden | Caller lacks required internal privilege. |
| **`NOT_FOUND` (5)** | 404 Not Found | Specified entity ID does not exist. |
| **`UNAVAILABLE` (14)** | 503 Unavailable | Target microservice container is offline. |

### 5.4 Exhaustive Protobuf Definition (`.proto`)

```protobuf
// aegisos/proto/cto_service.proto
syntax = "proto3";

package verdis.cto.v1;

option go_package = "verdis/cto/v1;ctov1";

// Service managing 9-Step CTO Pipeline execution across AI agents.
service TaskOrchestratorService {
  rpc ExecutePipelineStep (PipelineStepRequest) returns (PipelineStepResponse);
  rpc StreamStepLogs (LogStreamRequest) returns (stream LogChunk);
}

message PipelineStepRequest {
  string task_id = 1;
  uint32 step_number = 2;
  string component_name = 3;
  bytes payload_json = 4;
}

message PipelineStepResponse {
  string task_id = 1;
  uint32 step_number = 2;
  bool is_successful = 3;
  string gpt_verdict = 4;
  string execution_summary = 5;
}

message LogStreamRequest {
  string task_id = 1;
}

message LogChunk {
  string task_id = 2;
  string log_level = 3;
  string message = 4;
  int64 timestamp_epoch_ms = 5;
}
```

---

## 6. AUTHENTICATION, AUTHORIZATION & RATE LIMITING

### 6.1 Bearer Token Authentication Flow
All REST and gRPC API calls require an HTTP `Authorization` header containing a valid short-lived JWT token:

```http
GET /api/v1/tasks HTTP/1.1
Host: verdis.network
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

### 6.2 Rate Limiting Specifications (100 req/min Default)
API rate limiting protects backend infrastructure from overload:
- **Default Client Window:** **100 requests per minute** per client IP or JWT `sub` ID.
- **High-Priority Agents:** AI Sub-Agents operating in the CTO Pipeline receive a rate allowance of **1,000 requests per minute**.
- **Exceeding Limits:** Returns HTTP `429 Too Many Requests` with a JSON error payload and explicit retry window.

### 6.3 Rate Limiting Response Headers
Every REST API response contains the following operational headers:
- `X-RateLimit-Limit`: Maximum requests permitted per 60-second window (e.g. `100`).
- `X-RateLimit-Remaining`: Number of requests remaining in current window (e.g. `84`).
- `X-RateLimit-Reset`: Unix epoch timestamp when the current window resets.

---

## 7. API DOCUMENTATION REQUIREMENTS

### 7.1 Mandatory OpenAPI 3.1 Specification
All REST API endpoints written in FastAPI automatically expose interactive OpenAPI 3.1 JSON and Swagger UI interfaces:
- **Interactive Documentation Path:** `https://verdis.network/docs`
- **Raw OpenAPI Schema Path:** `https://verdis.network/api/v1/openapi.json`
- **Requirement:** Every route function must include explicit docstrings, Pydantic type annotations, `response_model` definitions, and example payloads.

### 7.2 AsyncAPI Specification for WebSockets/SSE
Event streaming channels (WebSockets & SSE) must publish an AsyncAPI 2.6 specification document in `docs/asyncapi.yaml` detailing channel topics, event payload schemas, and authentication flows.

### 7.3 Complete OpenAPI 3.1 YAML Example

```yaml
# docs/openapi.yaml
openapi: 3.1.0
info:
  title: Verdis Ecosystem AegisOS API
  version: 1.0.0
  description: Public REST API for task orchestration and agent management.
paths:
  /api/v1/tasks:
    get:
      summary: List engineering tasks
      parameters:
        - name: page
          in: query
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Successful paginated response
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Task'
                  total_count:
                    type: integer
components:
  schemas:
    Task:
      type: object
      properties:
        task_id:
          type: string
        title:
          type: string
        status:
          type: string
```

---

## 8. API DESIGN & COMPLIANCE CHECKLISTS

### 8.1 REST API Compliance Checklist
- [ ] URI uses plural nouns and lowercase hyphenated formatting (`/api/v1/tasks`).
- [ ] Response body includes standard envelope (`success`, `data`, `error`, `timestamp_utc`).
- [ ] All input request payloads validated via Pydantic v2 schemas.
- [ ] Endpoint protected by JWT Bearer token authentication middleware.
- [ ] OpenAPI docs generated cleanly with zero schema errors.

### 8.2 JSON-RPC & WebSocket Compliance Checklist
- [ ] JSON-RPC method uses `namespace_methodName` formatting.
- [ ] JSON-RPC response returns standard `jsonrpc: "2.0"` payload.
- [ ] WebSocket connections enforce JWT token handshake validation.
- [ ] WebSocket server dispatches 30-second heartbeat `PING` frames.
- [ ] Public RPC interface restricts method access (`--rpc-methods=safe`).

---
*End of Governance Document 05 — Verdis Ecosystem Universal API Interface & Protocol Standards.*
