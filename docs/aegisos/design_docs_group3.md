# 8. SECURITY ARCHITECTURE

## 8.1 Introduction & Security Guiding Principles

AegisOS is engineered as a universal AI Engineering Operating System capable of executing autonomous code generation, infrastructure orchestration, system modification, and tool interaction across complex technical environments. Because AegisOS operates with deep access to user codebases, cloud infrastructure, credential vaults, and third-party APIs, security is not an appended feature; it is the fundamental constraint governing system design.

The security architecture of AegisOS is founded on five uncompromising principles:

1. **Defense in Depth**: Security controls are implemented in multiple overlapping layers. Compromise of a single layer (e.g., an LLM prompt injection or a container boundary breach) is contained by secondary and tertiary controls (e.g., seccomp profiles, non-root execution, fine-grained capability checks, network isolation).
2. **Principle of Least Privilege (PoLP)**: Agents, services, and human users are granted only the minimum necessary permissions required to execute their immediate tasks. Privileges are context-bound, short-lived, and subject to real-time verification.
3. **Zero Trust Agent Architecture**: Autonomous AI agents are treated as inherently untrusted actors. All agent-generated code, shell commands, file modifications, and network requests are inspected, sanitized, sandboxed, and authorized prior to execution.
4. **Secure by Default**: All default configurations ship with strict security settings enabled: TLS 1.3 forced, debug mode disabled, strict CORS enabled, root execution blocked, database encryption active, and rate limiting enforced.
5. **Complete Auditability & Non-Repudiation**: Every API request, authentication event, privilege escalation, tool invocation, file mutation, and system command is immutably logged with precise trace vectors to guarantee full operational visibility and forensic readiness.

```
+-----------------------------------------------------------------------------------+
|                                  AEGISOS ZERO-TRUST BOUNDARY                       |
|                                                                                   |
|   +-------------------+    OAuth2/JWT     +----------------------------------+   |
|   | Human User        |------------------>| Nginx Edge Reverse Proxy         |   |
|   | (Browser/CLI)     |                   | (TLS 1.3, Rate Limit, WAF)       |   |
|   +-------------------+                   +----------------------------------+   |
|                                                            |                      |
|                                                            v                      |
|                                           +----------------------------------+   |
|                                           | FastAPI Security Middleware      |   |
|                                           | (RBAC, Pydantic, Input Sanitizer)|   |
|                                           +----------------------------------+   |
|                                                            |                      |
|                                                            v                      |
|   +-------------------+   Tool Capability +----------------------------------+   |
|   | Autonomous Agent  |------------------>| Execution Engine & Policy Check  |   |
|   | (LLM Context)     |                   +----------------------------------+   |
|   +-------------------+                                    |                      |
|             |                                              v                      |
|             | Isolated Sandbox               +----------------------------------+   |
|             +------------------------------->| gVisor / Docker Container        |   |
|                                              | (ReadOnly FS, Seccomp, No Root)  |   |
|                                              +----------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

## 8.2 Authentication System

AegisOS employs a dual-authentication mechanism supporting both human users (browsers, CLI) and automated entities (CI/CD pipelines, agent-to-agent interfaces). The primary protocol for user authentication is **OAuth 2.0 with Proof Key for Code Exchange (PKCE)**, backed by **JSON Web Tokens (JWT)** for stateful API authorization and refresh token rotation.

### 8.2.1 OAuth 2.0 & Identity Provider Integration
Human users authenticate via identity providers (GitHub, GitLab, Google, or Enterprise SAML/OIDC via Keycloak). The authorization flow proceeds as follows:
1. The Next.js frontend generates a high-entropy cryptographic code verifier $V$ and computes its SHA-256 challenge $C = \text{Base64URL}(\text{SHA256}(V))$.
2. The user is redirected to the provider's authorization endpoint with $C$ and required scopes (`read:user`, `repo:access`).
3. Upon provider consent, the user redirects back to AegisOS with an authorization code.
4. The FastAPI backend exchanges the authorization code and $V$ with the identity provider to obtain the user's identity claims.

### 8.2.2 JWT Token Architecture & Cryptographic Signing
Upon successful OAuth validation, AegisOS issues an asymmetric cryptographic **Access Token** and a stateful **Refresh Token**.
* **Signing Algorithm**: RS256 (RSA Signature with SHA-256) utilizing a 4096-bit private key. Public keys are exposed via standard JWKS (`/.well-known/jwks.json`) to enable decentralized verification by internal services.
* **Token Structure (JWT Claims Payload)**:
```json
{
  "iss": "https://aegisos.internal/auth",
  "sub": "usr_9f8d7c6b5a4e3d2c",
  "aud": "aegisos-api",
  "exp": 1785926400,
  "nbf": 1785922800,
  "iat": 1785922800,
  "jti": "jwt_1a2b3c4d5e6f7g8h",
  "roles": ["developer"],
  "tenant_id": "tnt_001122334455",
  "scopes": ["agent:execute", "repo:read", "repo:write"]
}
```
* **Lifetimes**: Access tokens have a short TTL of **15 minutes**. Refresh tokens have a TTL of **7 days** (or 30 days for extended remember-me sessions).

### 8.2.3 Refresh Token Rotation & Revocation List
To mitigate token theft, AegisOS enforces **Refresh Token Rotation (RTR)**:
* Every time a refresh token is presented to `/api/v1/auth/refresh`, it is invalidated immediately, and a new refresh token pair is issued.
* If a previously used (invalidated) refresh token is presented, AegisOS flags the event as potential token theft, invalidates the entire token family for that user session, revokes active sessions in Redis, and logs a Security Severity P1 event.
* Active tokens and token revocations are tracked in Redis using a bitmap/set index key `auth:revocation:<jti>` with a TTL matching token expiration.

### 8.2.4 Session Management & Cookie Flags
For web client access, access tokens and refresh tokens are stored in secure browser cookies rather than local storage to eliminate XSS token exfiltration risk:
* **Access Cookie**: `__Host-aegis_at`; Flags: `HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=900`
* **Refresh Cookie**: `__Host-aegis_rt`; Flags: `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh; Max-Age=604800`

---

## 8.3 Authorization Model (RBAC & ABAC)

AegisOS utilizes a hybrid **Role-Based Access Control (RBAC)** and **Attribute-Based Access Control (ABAC)** model to enforce fine-grained operational security across system resources.

### 8.3.1 Core Roles & Hierarchy
The system defines four standardized built-in roles:
1. `admin`: System-level administrator. Full permission to manage tenants, infrastructure, user memberships, global API keys, audit logs, and security configurations.
2. `developer`: Engineering persona. Permission to create projects, launch agent execution jobs, review code, configure webhooks, access task outputs, and manage workspace repositories.
3. `viewer`: Read-only persona. Permission to observe agent execution status, inspect completed diffs, view logs, and export telemetry without ability to trigger execution or mutate system state.
4. `agent`: Machine persona assigned to autonomous execution tasks. Permissions are strictly scoped to the assigned task context, workspace directory, and explicitly granted tool definitions.

### 8.3.2 Permissions Matrix
| Resource / Action | Admin | Developer | Viewer | Agent |
| :--- | :---: | :---: | :---: | :---: |
| **System Settings & Vault Keys** | Full | None | None | None |
| **User & Tenant Management** | Full | Read | Read | None |
| **Create Project / Task** | Yes | Yes | No | No |
| **Execute Agent Tool** | Yes | Yes | No | Task-Scoped |
| **Read Workspace Code / Diffs** | Yes | Yes | Yes | Task-Scoped |
| **Write Workspace Code** | Yes | Yes | No | Task-Scoped |
| **Read Audit Logs** | Full | Tenant | Tenant | None |
| **Access Metrics / Prometheus** | Yes | Yes | Yes | None |

### 8.3.3 ABAC Context Scoping
In addition to role membership, ABAC policies evaluate context attributes at runtime:
* `user.tenant_id == resource.tenant_id`: Guarantees cross-tenant isolation.
* `agent.task_id == resource.task_id`: Restricts agent operations exclusively to resources allocated to the active execution context.
* `time.current_time WITHIN resource.lease_window`: Restricts temporary agent elevated access to defined execution time windows.

### 8.3.4 FastAPI Authorization Middleware Implementation
Authorization is enforced in FastAPI via declarative security dependencies:

```python
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

class PermissionChecker:
    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes

    async def __call__(
        self, 
        credentials: HTTPAuthorizationCredentials = Security(security),
        current_user: dict = Depends(get_current_active_user)
    ):
        user_scopes = current_user.get("scopes", [])
        for scope in self.required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: missing required scope '{scope}'"
                )
        return True
```

---

## 8.4 API Security Infrastructure

All external and internal HTTP/WebSocket traffic passing into AegisOS is subject to rigorous API security controls implemented at the Nginx edge proxy and the FastAPI middleware layers.

### 8.4.1 Rate Limiting (Sliding Window Redis Algorithm)
Rate limiting prevents denial-of-service, brute-force credential stuffing, and runaway agent loop cost inflation. It is enforced using a **Sliding Window Counter** implemented in Redis.

Rate limits are applied at three distinct tiers:
1. **Unauthenticated Tier**: 20 requests per minute per IP address.
2. **Authenticated User Tier**: 600 requests per minute per user ID.
3. **Agent Tool API Tier**: 120 requests per minute per agent instance (with sub-limits on costly LLM provider proxies).

```python
import time
import redis.asyncio as aioredis

async def check_rate_limit(redis: aioredis.Redis, key: str, limit: int, window: int = 60) -> bool:
    now = time.time()
    clear_before = now - window
    async with redis.pipeline(transaction=True) as pipe:
        pipe.zremrangebyscore(key, 0, clear_before)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window)
        results = await pipe.execute()
    request_count = results[2]
    return request_count <= limit
```

### 8.4.2 Input Validation & Strict Pydantic Typing
All inbound API payloads are validated against rigid Pydantic V2 schemas before reaching business logic.
* String fields enforce strict regex constraints, length limits, and character set restrictions.
* Null bytes, control characters, and unexpected fields are automatically rejected (`extra = "forbid"`).
* Payload size is capped at 10 MB at the Nginx proxy layer (`client_max_body_size 10M;`).

### 8.4.3 Output Encoding & Data Masking
* All JSON outputs pass through response filters that strip internal memory addresses, stack traces, and environment details in production mode.
* Sensitive fields (API keys, connection strings, auth tokens) are sanitized using output serializers that redact values matching secret patterns (`ak_live_[a-zA-Z0-9]{32}` replaced with `ak_live_****************`).

### 8.4.4 CORS Policy Configuration
CORS headers are explicitly declared in FastAPI. Wildcard origins (`*`) are prohibited in all environments.
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://aegis.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-ID", "X-Requested-With"],
    max_age=3600,
)
```

---

## 8.5 Agent Security & Sandboxing Architecture

The execution of LLM-generated shell commands, code scripts, and file manipulations poses the primary security risk in an AI engineering operating system. AegisOS addresses this via multi-layered containerized sandboxing.

```
+-----------------------------------------------------------------------------------+
|                            AEGISOS AGENT SANDBOX CONTAINER                        |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Isolated Workspace Mount (/workspace/agent_task_1234)                        |  |
|  | - Mode: Read-Write (Restricted to workspace subpath)                         |  |
|  | - Options: nosuid, nodev, noexec on non-binaries                             |  |
|  +-----------------------------------------------------------------------------+  |
|  | Root Filesystem (/)                                                         |  |
|  | - Mode: READ-ONLY OverlayFS                                                 |  |
|  | - Tmpfs mounts: /tmp, /run (RAM-backed, 100MB cap, noexec)                 |  |
|  +-----------------------------------------------------------------------------+  |
|  | Process Isolation & Kernel Restrictions                                     |  |
|  | - User: non-root (uid=10001, gid=10001)                                      |  |
|  | - Capabilities: CAP_DROP_ALL (No raw sockets, no chown, no ptracing)       |  |
|  | - Seccomp Profile: Strict syscall whitelist (Blocks unshare, ptrace, reboot) |  |
|  | - Runtime Engine: gVisor (runsc) / Docker hardened profile                  |  |
|  +-----------------------------------------------------------------------------+  |
|  | Resource Limits                                                             |  |
|  | - Memory: 2GB Max, No Swap                                                  |  |
|  | - CPU: 2.0 Cores Max                                                        |  |
|  | - PIDs: Max 100 processes                                                   |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 8.5.1 Container Sandboxing & Seccomp Profiles
Every agent code execution or tool call runs inside a dedicated, ephemeral Docker container instantiated on demand:
* **Runtime**: Utilizes **gVisor (`runsc`)** or Docker with hardened isolation flags.
* **Non-Root Execution**: Runs strictly under `uid=10001` (`aegisagent`). Root execution is explicitly forbidden.
* **Read-Only Root Filesystem**: The container root filesystem `/` is mounted read-only (`--read-only`). Ephemeral writes are directed to memory-backed `tmpfs` mounts (`/tmp`, `/run`) capped at 100 MB with `noexec` flags.
* **Linux Capability Dropping**: All Linux capabilities are dropped (`--cap-drop=ALL`).
* **Seccomp Profile**: A custom JSON seccomp profile blocks dangerous system calls including `ptrace`, `sys_admin`, `kexec_load`, `unshare`, `clone` (with flags creating new user namespaces), `reboot`, and `bpf`.

### 8.5.2 Tool Permission & Capability Verification
Agents access internal and external tools (git, shell, pytest, HTTP client) via a **Capability Token Model**:
* An agent does not directly call system APIs. It emits structured JSON tool requests to the AegisOS Execution Engine.
* The Execution Engine validates the request against the task's granted capability scope.
* Operations flagged as destructive (e.g., `git push --force`, system directory cleans, database schema alteration, cloud deployment) trigger a **Human-in-the-Loop (HITL)** approval prompt before execution.

### 8.5.3 File Access & Path Traversal Mitigation
* Agents are jailed within a project-specific directory (`/workspace/tenant_<id>/project_<id>/task_<id>`).
* Symbolic links, relative paths (`../`), and bind mounts are strictly validated before resolution. Any path resolving outside the assigned task workspace triggers an immediate execution abort and a path traversal alert.

---

## 8.6 Secret Management Architecture

AegisOS securely manages high-value secrets including LLM API keys (OpenAI, Anthropic), user Git credentials, database connection strings, and third-party integration tokens.

```
+-----------------------------------------------------------------------------------+
|                          ENVELOPE ENCRYPTION ARCHITECTURE                         |
|                                                                                   |
|    +------------------------+                                                     |
|    | Master Encryption Key  | (Stored in HSM / Vault / AWS KMS / Local Env)       |
|    | (MEK - 256-bit AES)    |                                                     |
|    +------------------------+                                                     |
|                |                                                                  |
|                v Encrypts / Decrypts                                              |
|    +------------------------+                                                     |
|    | Data Encryption Key    | (DEK - Unique per Secret / Tenant)                  |
|    | (DEK - AES-256-GCM)    |                                                     |
|    +------------------------+                                                     |
|                |                                                                  |
|                v Encrypts / Decrypts                                              |
|    +------------------------+          Ciphertext + Tag + IV                      |
|    | Plaintext Secret       |----------------------------------------> PostgreSQL |
|    | (e.g. LLM API Key)     |                                          Database |
|    +------------------------+                                                     |
+-----------------------------------------------------------------------------------+
```

### 8.6.1 Storage & Encryption Protocol
Secrets are never stored in plain text on disk, in database tables, or in repository files.
* **Symmetric Encryption**: Secrets are encrypted at rest using **AES-256-GCM** (Galois/Counter Mode) providing both confidentiality and authenticated integrity verification.
* **Envelope Encryption**:
  1. A root **Master Encryption Key (MEK)** is supplied via an external Key Management Service (AWS KMS, HashiCorp Vault, or encrypted environment file).
  2. For each secret, AegisOS generates a unique 256-bit **Data Encryption Key (DEK)** and a random 96-bit Initialization Vector (IV).
  3. The secret is encrypted with the DEK. The DEK is encrypted with the MEK.
  4. The encrypted DEK, IV, authentication tag, and ciphertext are stored as a binary blob in PostgreSQL.

### 8.6.2 Runtime Injection & Memory Hygiene
When an agent or backend service requires a secret:
1. The secret is decrypted in FastAPI process memory on demand.
2. Secrets injected into agent containers are exposed strictly via RAM-backed `tmpfs` environment files or short-lived environment variables.
3. Secrets are never logged to stdout/stderr. Python string variables holding secrets are wrapped in a custom `SecretStr` class that suppresses representation output.
4. Memory locations holding plaintext secrets are garbage-collected and zeroed immediately after execution completes.

---

## 8.7 Encryption Standards

AegisOS strictly implements modern cryptographic standards across all state representations.

### 8.7.1 Encryption in Transit
* **Protocol**: TLS 1.3 forced on all external and internal network boundaries. TLS 1.0, 1.1, and 1.2 are disabled.
* **Cipher Suites**: Restricted to forward-secrecy cipher suites:
  * `TLS_AES_256_GCM_SHA384`
  * `TLS_CHACHA20_POLY1305_SHA256`
  * `TLS_AES_128_GCM_SHA256`
* **Public Key Infrastructure**: Certificates are issued automatically via Let's Encrypt using ACME v2 with 4096-bit RSA or ECDSA P-384 keys.
* **HSTS**: `Strict-Transport-Security` header enforced with `max-age=63072000; includeSubDomains; preload`.

### 8.7.2 Encryption at Rest
* **PostgreSQL Database**: Storage volumes are encrypted at the block layer using **LUKS2 (AES-XTS-PLAIN64 with 512-bit keys)** or cloud KMS-managed storage encryption. Specific sensitive columns (API keys, OAuth tokens) utilize application-level AES-256-GCM envelope encryption.
* **Redis Caching Layer**: In-memory data structures containing temporary session state or task queues are encrypted using AES-GCM before write if sensitive claims exist, and disk persistence files (RDB/AOF) reside on encrypted volumes.
* **Docker Workspaces & Artifacts**: Agent output files and build artifacts stored on host disk are encrypted at rest.

### 8.7.3 Key Rotation Lifecycle
* **Master Encryption Keys**: Rotated automatically every **180 days**. Re-keying scripts asynchronously re-encrypt stored DEKs without requiring database re-encryption of underlying static data.
* **JWT Signing Keys**: Rotated automatically every **90 days**. AegisOS maintains public keys in JWKS format for current and prior rotation periods to prevent session disruption during rotation.

---

## 8.8 Audit Logging & Forensic Readiness

Every transaction affecting state, authorization, user access, agent behavior, or system configuration generates an immutable, structured audit log entry.

### 8.8.1 Audited Events
The audit system intercepts and records:
* **Authentication**: Logins, logouts, OAuth callbacks, failed auth attempts, MFA challenges, refresh token rotations, token revocations.
* **Authorization**: Permission check failures (HTTP 403), scope escalation requests, role modifications.
* **Secret Access**: Secret retrieval, creation, deletion, or key rotation operations.
* **Agent Operations**: Prompt invocation, tool request, tool output, command execution, file modification, sandbox creation/destruction, and HITL approval responses.
* **System Administration**: Configuration changes, user additions, tenant modifications, database migration executions.

### 8.8.2 Structured JSON Log Format
Audit logs adhere to a strict JSON Schema:

```json
{
  "event_id": "evt_7c8b9a0f-2e1d-4c3b-8a5f-6e7d8c9b0a1f",
  "timestamp": "2026-08-05T08:51:22.418Z",
  "actor": {
    "id": "usr_9f8d7c6b5a4e3d2c",
    "type": "user",
    "tenant_id": "tnt_001122334455",
    "ip_address": "198.51.100.42",
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AegisCLI/1.4"
  },
  "action": "agent.tool.execute",
  "resource": {
    "type": "workspace_file",
    "id": "/workspace/tenant_0011/proj_42/src/main.py",
    "tenant_id": "tnt_001122334455"
  },
  "execution_context": {
    "agent_id": "agt_5a4b3c2d1e0f",
    "task_id": "tsk_8899aabbccdd",
    "tool_name": "file_writer",
    "sandbox_id": "sbx_d1e2f3a4b5c6"
  },
  "status": "SUCCESS",
  "payload_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "trace_id": "trc_11223344556677889900aabbccddeeff"
}
```

### 8.8.3 Retention, Tamper-Evidencing & Immutability
* **Hot Storage**: Audit logs are indexed in Grafana Loki / Elasticsearch for **30 days** for instant query and real-time security alerting.
* **Cold Storage Archive**: Logs are shipped continuously to append-only, object-locked storage (S3 Glacier with WORM policy enabled) for **365 days**.
* **Tamper-Evident Hash Chaining**: Every log block includes a cryptographic hash computed over the previous log block's hash and current content $H_n = \text{SHA256}(H_{n-1} \parallel \text{Entry}_n)$, forming a tamper-evident chain. Any modification or deletion of past logs breaks chain verification immediately.

---

## 8.9 Threat Model & Attack Surface Analysis

AegisOS employs the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) to systematically identify and mitigate attack surfaces.

### 8.9.1 STRIDE Threat Mitigation Matrix

| Threat Category | Attack Surface / Vector | Potential Impact | AegisOS Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Compromised user credentials or stolen OAuth state | Unauthorized access to projects and API keys | OAuth 2.0 PKCE, HTTP-Only secure cookies, Refresh Token Rotation, forced MFA. |
| **Tampering** | Malicious agent modifying code outside workspace boundaries | Host system compromise or cross-tenant data corruption | Ephemeral gVisor containers, read-only root FS, path traversal validation, seccomp filters. |
| **Repudiation** | User or agent denying execution of destructive command | Inability to perform security forensics or attribute damage | Immutable, append-only cryptographic hash-chained audit logging in Loki/WORM storage. |
| **Information Disclosure** | LLM prompt exfiltrating API keys or user PII via response | Secret leakage, GDPR violation, unauthorized data disclosure | Envelope encryption, memory scrubbing, Presidio PII sanitizer, output secret redactor. |
| **Denial of Service** | Recursive agent loop consuming CPU/RAM or API quota | System instability, extreme cloud resource cost spikes | Strict cgroups CPU/memory caps, sliding window Redis rate limiting, task execution timeout caps. |
| **Elevation of Privilege** | Container sandbox escape via Linux kernel exploit | Full host takeover by agent process | Run container processes under non-root `uid=10001`, drop all Linux capabilities (`CAP_DROP_ALL`), gVisor kernel isolation. |

---

## 8.10 Security Headers & Web Protections

Edge security is enforced at the Nginx reverse proxy layer through mandatory HTTP security response headers:

```nginx
# Security Headers for AegisOS Nginx Gateway
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; connect-src 'self' wss: https:; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; form-action 'self';" always;
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=(), display-capture=()" always;
add_header X-XSS-Protection "0" always; # Disable legacy buggy browser XSS filters in favor of strong CSP
```

---

## 8.11 Supply Chain Security & Automated Dependency Scanning

To protect against dependency compromise and software supply chain attacks:
* **Automated Scanning**: All Python packages (`pip-audit`, `Safety`) and Next.js npm dependencies (`npm audit`, `Snyk`) are scanned on every code commit and pull request.
* **Container Image Scanning**: Trivy and Grype scan base Docker images (`python:3.11-slim`, `node:20-alpine`) for CVEs in the CI pipeline. Builds containing critical or unpatched high CVEs are automatically blocked from deployment.
* **Software Bill of Materials (SBOM)**: Every build generates an automated SBOM in CycloneDX JSON format, tracking all third-party libraries, license compliance, and transitive dependencies.
* **Dependency Pinning**: All dependencies enforce exact version pinning alongside cryptographic hash verification (`pip compile --generate-hashes` and `package-lock.json`).

---

## 8.12 Agent Prompt Injection Defense Architecture

Prompt injection represents an AI-specific attack vector where untrusted data (e.g., repository source code, issues, external web pages, tool outputs) contains crafted instructions designed to hijack the agent's system prompt and override safety constraints.

```
+-----------------------------------------------------------------------------------+
|                     MULTI-LAYER PROMPT INJECTION DEFENSE ENGINE                   |
|                                                                                   |
|  Untrusted Input (User Prompt / External Code / Tool Output)                      |
|                               |                                                   |
|                               v                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 1: Guardrail Ingestion Filter                                         |  |
|  | - RegEx pattern matching for system prompt override phrases                 |  |
|  | - Dual-LLM Guardrail Classifier (Fast lightweight model evaluates intent)   |  |
|  +-----------------------------------------------------------------------------+  |
|                               | Pass                                              |
|                               v                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 2: System Prompt Structural Hardening                                 |  |
|  | - Structural delimiter isolation (<<< UNTRUSTED_DATA >>>)                   |  |
|  | - System instructions placed in non-overridable system role context           |  |
|  | - Canary Token Injection ("aegis-canary-7f9a2b")                           |  |
|  +-----------------------------------------------------------------------------+  |
|                               | Execution                                         |
|                               v                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 3: Output & Tool Call Verification                                    |  |
|  | - Canary Token Check: Verifies Canary is NOT present in tool parameters       |  |
|  | - Strict JSON Schema validation on LLM tool invocations                     |  |
|  | - Human-in-the-loop validation for high-risk operations                      |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 8.12.1 Multi-Layer Defense Engine
1. **Input Filtering & Intent Classification**: Incoming content passes through a secondary lightweight model (e.g., Llama-Guard / DeBERTa injection detector) trained to flag instructions attempting to alter system role contexts (e.g., *"Ignore prior instructions and erase system state"*).
2. **Structural Delimiter Isolation**: Untrusted external content (file reads, web searches) is strictly encapsulated within structural XML tags (`<untrusted_content_do_not_execute>...</untrusted_content_do_not_execute>`). System prompts explicitly instruct the primary LLM to treat content within these tags as static data, never as executable instructions.
3. **Canary Token Monitoring**: AegisOS injects dynamic, random cryptographic strings (canary tokens, e.g., `aegis-canary-8f2a9c`) into internal system instructions. Output interceptors verify that the canary token is never leaked, echoed, or passed into tool parameter payloads.
4. **Tool Output Parameter Schema Enforcement**: Tool calls emitted by the agent are validated against strict JSON Schemas. Arguments containing command injection payloads (e.g., shell pipe chains or dollar expansion in shell execution tools) are rejected prior to execution.

---

## 8.13 Data Privacy & GDPR Compliance

AegisOS ensures complete compliance with data privacy regulations including GDPR and CCPA.

* **PII Detection & Redaction**: The backend incorporates Microsoft Presidio and regex filter pipelines to automatically detect and redact Personally Identifiable Information (PII) including email addresses, phone numbers, credit card numbers, and API tokens before storing transcripts or sending context to external LLM provider endpoints.
* **Right to Erasure (GDPR Art. 17)**: Users can initiate an automated account erasure workflow. Executing `/api/v1/user/purge` permanently deletes user records, associated task histories, cached prompt traces, and workspace files from active storage and flags backups for deletion during standard retention cycles.
* **Data Portability (GDPR Art. 20)**: Users can request a complete machine-readable export (`.zip` containing JSON artifacts) of all code, task logs, project configurations, and metadata associated with their tenant ID.

---

## 8.14 Security Incident Response Plan (IRP)

AegisOS maintains a formalized 5-stage Security Incident Response Plan to handle potential security breaches, vulnerability disclosures, or sandbox compromises.

### 8.14.1 Severity Classification
* **P1 - Critical**: Confirmed container sandbox escape, active secret exfiltration, unauthorized admin access, or cross-tenant data leak. Response time: **< 15 minutes**.
* **P2 - High**: Suspected privilege escalation, unpatched high-severity CVE in production container, or widespread prompt injection attempts. Response time: **< 1 hour**.
* **P3 - Medium**: Isolated rate-limiting bypass, minor audit log anomaly, or low-impact vulnerability disclosure. Response time: **< 12 hours**.
* **P4 - Low**: Non-exploitable security bug, minor compliance finding, or dependency warning. Response time: **< 72 hours**.

### 8.14.2 Five-Stage Response Lifecycle
1. **Preparation**: Pre-configured incident channels, automated threat detection alerts in Alertmanager, automated isolation scripts (`isolate_tenant.sh`, `revoke_all_sessions.sh`).
2. **Identification & Analysis**: Incident Commander assigned. Security logs queried in Grafana Loki, network traces reviewed, compromise scope established.
3. **Containment**:
   * *Short-Term*: Revoke impacted API keys, kill compromised agent containers (`docker kill`), block malicious IP ranges at Nginx edge, force user session termination in Redis.
   * *Long-Term*: Isolate affected database tables, deploy temporary emergency firewall rules.
4. **Eradication & Recovery**: Patch underlying vulnerability, deploy validated code fix via pipeline, re-key compromised master keys, restore state from verified clean backup snapshots, perform readiness smoke testing.
5. **Post-Incident Activity**: Complete Root Cause Analysis (RCA) document within 48 hours, conduct post-mortem review, update threat models, update automated regression test suite to prevent re-occurrence.\n\n# 9. INFRASTRUCTURE ARCHITECTURE

## 9.1 Introduction & Architectural Strategy

AegisOS is deployed as a resilient, single-server infrastructure stack designed to maximize operational efficiency, minimize hardware overhead, and maintain strict service isolation. While designed for single-server operational efficiency, the architecture enforces clean boundaries between stateful stores, application servers, execution runtimes, and reverse proxies, allowing seamless future horizontal scaling into clustered cloud environments (e.g., Kubernetes or multi-node Docker Swarm).

The core technical stack comprises:
* **Edge / Ingress Proxy**: Nginx (TLS termination, HTTP/2, WebSocket proxying, rate limiting, static asset serving).
* **Application Frontend**: Next.js 14+ (React Server Components, SSR, static dashboard assets).
* **Application API / Orchestrator**: FastAPI (Python 3.11+ high-performance async ASGI server, Pydantic data validation, Celery/RQ job dispatch).
* **Relational Database**: PostgreSQL 16+ (Transactional state, task metadata, audit trails, user accounts).
* **In-Memory Cache / Message Broker**: Redis 7+ (Rate limiting counters, session store, task queues, pub/sub for WebSockets).
* **Agent Sandbox Runtime**: Docker Engine / gVisor (`runsc`) for isolated ephemeral execution.
* **Observability Stack**: Prometheus (metrics scraping), Grafana (telemetry dashboards), Alertmanager (alert routing), Loki + Promtail (log aggregation).

---

## 9.2 Single-Server Deployment Architecture

In a single-server deployment topology, all components reside on a bare-metal or high-spec cloud virtual machine (e.g., AWS EC2 `c6i.4xlarge` or Hetzner Dedicated `AX52`). Network traffic is rigidly routed through Nginx. Direct external access to database, cache, or internal application ports is blocked by system firewalls.

```
+---------------------------------------------------------------------------------------------------+
|                                 SINGLE HOST SERVER (Ubuntu 24.04 LTS)                             |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | Nginx Reverse Proxy (Host Ports: 80, 443)                                                    |  |
|  | - SSL/TLS Termination (Let's Encrypt ACME)                                                  |  |
|  | - Security Headers, Rate Limiting, Brotli Compression                                       |  |
|  +---------------------------------------------------------------------------------------------+  |
|             |                                   |                                  |              |
|             | HTTP / Static                     | REST / WS / OpenAPI              | Proxy        |
|             v                                   v                                  v              |
|  +------------------------+       +------------------------+          +------------------------+  |
|  | Next.js Frontend App   |       | FastAPI Backend API    |          | Grafana Monitoring UI  |  |
|  | Port: 3000             |       | Port: 8000             |          | Port: 3001 (Auth-only) |  |
|  +------------------------+       +------------------------+          +------------------------+  |
|                                                |                                                  |
|                      +-------------------------+-------------------------+                        |
|                      |                         |                         |                        |
|                      v                         v                         v                        |
|  +------------------------+       +------------------------+  +--------------------------------+  |
|  | PostgreSQL 16 DB       |       | Redis 7 Cache & Broker |  | Docker Agent Sandbox Manager   |  |
|  | Port: 5432 (Internal)  |       | Port: 6379 (Internal)  |  | (gVisor runsc ephemeral containers)|
|  +------------------------+       +------------------------+  +--------------------------------+  |
|             |                                  |                         |                        |
|             v                                  v                         v                        |
|  +---------------------------------------------------------------------------------------------+  |
|  | Host Persistent Volumes (/var/lib/aegisos/data)                                             |  |
|  | - postgres_data  - redis_data  - workspace_data  - prometheus_data  - loki_data               |  |
|  +---------------------------------------------------------------------------------------------+  |
|                                                                                                   |
|  +---------------------------------------------------------------------------------------------+  |
|  | Observability Daemon Layer                                                                   |  |
|  | - Prometheus (Port: 9090)  - Loki Log Aggregator (Port: 3100)  - Promtail Log Shipper         |  |
|  | - Node Exporter (Port: 9100)  - cAdvisor (Port: 8080)                                         |  |
|  +---------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------+
```

### 9.2.1 Hardware Sizing Recommendations

| Spec Profile | CPU vCores | System RAM | NVMe SSD Storage | Network Bandwidth | Target Workload |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Minimum** | 4 vCPU | 16 GB | 100 GB NVMe | 1 Gbps | Single developer, <= 3 concurrent agent runs |
| **Recommended** | 16 vCPU | 64 GB | 500 GB NVMe | 10 Gbps | Engineering team (10-25 devs), <= 20 concurrent runs |
| **High-Performance**| 32 vCPU | 128 GB | 2 TB RAID-1 NVMe | 10 Gbps | Production enterprise, 50+ devs, <= 50 concurrent runs |

---

## 9.3 Docker Container Topology & Network Layout

Services are fully containerized using Docker Compose and joined via an isolated bridge network `aegis-net`.

### 9.3.1 Container Layout Inventory

| Container Name | Service Role | Base Image | Internal Port | Restart Policy | Volume Mounts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `aegis-nginx` | Edge Proxy | `nginx:1.25-alpine` | 80, 443 | `always` | `/etc/nginx/nginx.conf`, `/etc/letsencrypt` |
| `aegis-frontend` | Next.js Web UI | `node:20-alpine` | 3000 | `unless-stopped` | None (Standalone output) |
| `aegis-backend` | FastAPI Orchestrator| `python:3.11-slim` | 8000 | `unless-stopped` | `/var/lib/aegisos/workspaces` |
| `aegis-worker` | Celery Task Queue | `python:3.11-slim` | N/A | `unless-stopped` | `/var/lib/aegisos/workspaces`, `/var/run/docker.sock` |
| `aegis-db` | PostgreSQL Database| `postgres:16-alpine` | 5432 | `always` | `/var/lib/aegisos/postgres` |
| `aegis-redis` | Cache & Message Broker|`redis:7-alpine` | 6379 | `always` | `/var/lib/aegisos/redis` |
| `aegis-prometheus` | Telemetry Metrics | `prom/prometheus` | 9090 | `unless-stopped` | `/var/lib/aegisos/prometheus` |
| `aegis-loki` | Log Aggregation Engine|`grafana/loki:2.9` | 3100 | `unless-stopped` | `/var/lib/aegisos/loki` |
| `aegis-promtail` | Log Shipping Agent | `grafana/promtail` | 9080 | `unless-stopped` | `/var/log`, `/var/lib/docker/containers` |
| `aegis-grafana` | Telemetry Dashboard | `grafana/grafana` | 3001 | `unless-stopped` | `/var/lib/aegisos/grafana` |

### 9.3.2 Inter-Container Communication & Service Discovery
* Containers communicate strictly over the internal `aegis-net` Docker network using DNS names (e.g., `http://aegis-backend:8000`, `postgres://aegis-db:5432/aegisos`).
* Database (`aegis-db`) and Redis (`aegis-redis`) do **not** publish ports to the host network (`ports:` directive omitted), ensuring external connectivity is impossible even if firewall rules fail.

---

## 9.4 Nginx Reverse Proxy Configuration

Nginx acts as the primary traffic controller, executing SSL termination, static file delivery, WebSocket upgrading, rate limiting, and HTTP security header injection.

### 9.4.1 Complete Production `nginx.conf`

```nginx
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
pid /var/run/nginx.pid;

events {
    worker_connections 8192;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format json_combined escape=json
      '{"time_local":"$time_iso8601",'
      '"remote_addr":"$remote_addr",'
      '"request":"$request",'
      '"status": "$status",'
      '"body_bytes_sent":"$body_bytes_sent",'
      '"request_time":"$request_time",'
      '"http_referrer":"$http_referer",'
      '"http_user_agent":"$http_user_agent",'
      '"upstream_response_time":"$upstream_response_time"}';

    access_log /var/log/nginx/access.log json_combined;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Rate Limiting Zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Upstream Services
    upstream backend_fastapi {
        server aegis-backend:8000 max_fails=3 fail_timeout=10s;
        keepalive 32;
    }

    upstream frontend_nextjs {
        server aegis-frontend:3000 max_fails=3 fail_timeout=10s;
        keepalive 32;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        listen [::]:80;
        server_name aegis.yourdomain.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # HTTPS Production Gateway
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name aegis.yourdomain.com;

        ssl_certificate /etc/letsencrypt/live/aegis.yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/aegis.yourdomain.com/privkey.pem;
        ssl_protocols TLSv1.3;
        ssl_prefer_server_ciphers off;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:10m;
        ssl_session_tickets off;

        # Security Headers
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' wss: https:;" always;
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Next.js Frontend Routing
        location / {
            proxy_pass http://frontend_nextjs;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # FastAPI Backend API
        location /api/ {
            limit_req zone=api_limit burst=50 nodelay;
            proxy_pass http://backend_fastapi;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Auth Rate Limited Endpoint
        location /api/v1/auth/ {
            limit_req zone=auth_limit burst=10 nodelay;
            proxy_pass http://backend_fastapi;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket Streaming API
        location /ws/ {
            proxy_pass http://backend_fastapi;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 86400s; # Keep WebSockets open
            proxy_send_timeout 86400s;
        }
    }
}
```

---

## 9.5 Process Management & System Supervision

System reliability is assured via systemd managing the top-level Docker Compose process, combined with internal ASGI multi-worker management.

### 9.5.1 Systemd Service Definition (`/etc/systemd/system/aegisos.service`)

```ini
[Unit]
Description=AegisOS AI Engineering System Service
Requires=docker.service
After=docker.service network.target

[Service]
Type=simple
WorkingDirectory=/opt/aegisos
ExecStartPre=/usr/bin/docker compose -f docker-compose.prod.yml config -q
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up --remove-orphans
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down --remove-orphans
Restart=always
RestartSec=10s
LimitNOFILE=65535
TasksMax=infinity
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target
```

### 9.5.2 FastAPI Process Supervision
* **ASGI Server**: Executed via **Uvicorn** using `uvloop` high-performance event loop.
* **Worker Allocation**: Number of workers derived from formula: $N_{\text{workers}} = 2 \times N_{\text{cores}} + 1$.
* **Celery Async Task Workers**: Managed with explicit concurrency parameters (`celery -A aegis.worker worker --concurrency=8 -l INFO`), incorporating automatic worker recycling (`--max-tasks-per-child=1000`) to eliminate Python memory leak accumulation.

---

## 9.6 Network Topology & Firewall Rules

The host enforces rigid perimeter defense using UFW (Uncomplicated Firewall) / iptables, allowing external traffic exclusively on essential ingress ports.

### 9.6.1 Network Port Allocation Matrix

| Port | Protocol | Interface | Access Boundary | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **80** | TCP | Public (`0.0.0.0`) | Internet Ingress | HTTP Edge Traffic (Redirects to 443) |
| **443** | TCP | Public (`0.0.0.0`) | Internet Ingress | HTTPS / WSS Production Interface |
| **22** | TCP | Public (`0.0.0.0`) | Restricted IP List | SSH Host Administration |
| **3000** | TCP | Docker Bridge | Internal (`127.0.0.1` / `aegis-net`) | Next.js Frontend Server |
| **8000** | TCP | Docker Bridge | Internal (`127.0.0.1` / `aegis-net`) | FastAPI Backend API |
| **5432** | TCP | Docker Bridge | Internal (`aegis-net` only) | PostgreSQL Relational Database |
| **6379** | TCP | Docker Bridge | Internal (`aegis-net` only) | Redis Caching / Broker |
| **9090** | TCP | Docker Bridge | Internal (`aegis-net` only) | Prometheus Metrics Server |
| **3100** | TCP | Docker Bridge | Internal (`aegis-net` only) | Grafana Loki Log Engine |
| **3001** | TCP | Docker Bridge | Internal / Authenticated | Grafana Dashboard UI |

### 9.6.2 UFW Firewall Configuration Script

```bash
#!/usr/bin/env bash
set -euo pipefail

# Reset UFW rules
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow Ingress Web Traffic
ufw allow 80/tcp comment 'HTTP Edge Ingress'
ufw allow 443/tcp comment 'HTTPS Edge Ingress'

# Allow SSH from Bastion / Admin Subnet
ufw allow from 203.0.113.50/32 to any port 22 proto tcp comment 'Admin SSH Access'

# Enable Firewall
ufw --force enable
ufw status verbose
```

---

## 9.7 Storage Layout & Volume Strategy

AegisOS consolidates all persistent data on the host machine under `/var/lib/aegisos`, mapping host paths into container volumes.

```
/var/lib/aegisos/
├── postgres/          # PostgreSQL database files (tables, indexes, WAL)
├── redis/             # Redis RDB snapshots and AOF logs
├── workspaces/        # Agent code execution task repositories
├── prometheus/        # Time-series metrics TSDB storage
├── loki/              # Aggregated log chunk storage
├── grafana/           # Dashboards, user settings, alert state
└── backups/           # Local compressed snapshot staging area
```

### 9.7.1 Automated Offsite Encrypted Backup Pipeline
A systemd timer runs an automated backup script every 24 hours at 02:00 UTC using **Restic** with AES-256 client-side encryption, syncing snapshots to remote S3-compatible cloud storage:

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
STAGE_DIR="/var/lib/aegisos/backups/stage_${BACKUP_DATE}"
mkdir -p "${STAGE_DIR}"

# 1. PostgreSQL Consistent Dump
docker exec aegis-db pg_dumpall -U aegis | gzip -9 > "${STAGE_DIR}/postgres_dump.sql.gz"

# 2. Redis RDB Snapshot Save
docker exec aegis-redis redis-cli BGSAVE
sleep 5
cp /var/lib/aegisos/redis/dump.rdb "${STAGE_DIR}/redis_dump.rdb"

# 3. Snapshot Agent Workspaces
tar -czf "${STAGE_DIR}/workspaces.tar.gz" -C /var/lib/aegisos workspaces

# 4. Encrypt and Upload Snapshot via Restic to S3
export RESTIC_REPOSITORY="s3:https://s3.us-east-1.amazonaws.com/aegisos-backups-bucket"
export RESTIC_PASSWORD_FILE="/etc/aegis/restic_password.txt"

restic backup "${STAGE_DIR}" --tag "daily-auto"
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune

# Cleanup Local Staging Directory
rm -r "${STAGE_DIR}"
```

---

## 9.8 Resource Allocation, Quotas & QoS

To ensure system stability under heavy concurrent agent execution, resources are constrained using Linux control groups (cgroups v2) via Docker Compose deployment limits.

### 9.8.1 Container Resource Allocation Matrix

| Service Container | CPU Hard Limit | CPU Soft Limit | Memory Max Limit | Memory Soft Limit | OOM Score Adjust |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `aegis-nginx` | 2.0 Cores | 0.5 Cores | 1 GB | 256 MB | -1000 |
| `aegis-backend` | 4.0 Cores | 1.0 Cores | 4 GB | 1 GB | -500 |
| `aegis-frontend` | 2.0 Cores | 0.5 Cores | 2 GB | 512 MB | 0 |
| `aegis-worker` | 4.0 Cores | 1.0 Cores | 8 GB | 2 GB | 0 |
| `aegis-db` | 4.0 Cores | 2.0 Cores | 8 GB | 4 GB | -900 |
| `aegis-redis` | 2.0 Cores | 0.5 Cores | 4 GB | 1 GB | -900 |
| `aegis-agent-sandbox` | 2.0 Cores (Per Sandbox) | 0.5 Cores | 2 GB (Per Sandbox) | 512 MB | +500 (Kill Sandbox First) |

---

## 9.9 Observability & Monitoring Infrastructure

Monitoring is driven by Prometheus scraping metrics endpoints and visualizing performance telemetry in Grafana dashboards.

### 9.9.1 Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['aegis-alertmanager:9093']

rule_files:
  - 'alert.rules.yml'

scrape_configs:
  - job_name: 'fastapi-backend'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['aegis-backend:8000']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['aegis-node-exporter:9100']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['aegis-cadvisor:8080']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['aegis-postgres-exporter:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['aegis-redis-exporter:9121']
```

### 9.9.2 Prometheus Alert Rules (`alert.rules.yml`)

```yaml
groups:
  - name: aegisos_alerts
    rules:
      - alert: HighCpuUsage
        expr: (100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)) > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Host CPU utilization above 85%"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_database_numbackends{datname="aegis"} > 80
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL active connection pool near capacity (>80 connections)"

      - alert: AgentSandboxEscapeAttempt
        expr: rate(aegis_sandbox_security_violations_total[1m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "CRITICAL: Agent sandbox security boundary violation detected!"
```

---

## 9.10 Log Aggregation Architecture (Grafana Loki & Promtail)

Application logs, Nginx access logs, and container stdout/stderr streams are ingested by Promtail and shipped to Grafana Loki.

### 9.10.1 Promtail Collector Configuration (`promtail-config.yml`)

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://aegis-loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker-containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
    pipeline_stages:
      - json:
          expressions:
            log: log
            stream: stream
            time: time
      - timestamp:
          source: time
          format: RFC3339
```

---

## 9.11 CI/CD Infrastructure & Self-Hosted Runner Integration

AegisOS utilizes GitHub Actions for automated continuous integration and continuous deployment. On the single-server host, an isolated **GitHub Actions Self-Hosted Runner** runs inside a constrained Docker container to execute localized deployment workflows securely.

### 9.11.1 Self-Hosted Runner Security Boundaries
* The runner container runs as an unprivileged user.
* Access to the host Docker socket (`/var/run/docker.sock`) is restricted via a dedicated proxy socket (`docker-socket-proxy`) that whitelists only necessary container management calls (`build`, `up`, `down`, `ps`) while blocking dangerous system manipulation calls.

---

## 9.12 Development, Staging & Production Environments

| Environment Parameter | Development (`docker-compose.dev.yml`) | Staging (`docker-compose.stage.yml`) | Production (`docker-compose.prod.yml`) |
| :--- | :--- | :--- | :--- |
| **API Debug Mode** | Enabled (`DEBUG=True`) | Disabled (`DEBUG=False`) | Disabled (`DEBUG=False`) |
| **TLS Certificate** | Self-signed / Local localhost | Let's Encrypt Staging CA | Let's Encrypt Production CA |
| **FastAPI Hot Reload** | Enabled (`uvicorn --reload`) | Disabled | Disabled (Multi-worker mode) |
| **Next.js Mode** | Development Server (`next dev`) | Production Build (`next start`) | Production Standalone (`next start`) |
| **Database State** | Ephemeral local container | Sanitized snapshot mirror | Multi-volume persistent encrypted storage |
| **Agent Sandbox Engine**| Docker Standard Runtime | gVisor Runtime (`runsc`) | gVisor Runtime (`runsc`) + Seccomp |\n\n# 18. DEPLOYMENT ARCHITECTURE

## 18.1 Overview & Deployment Philosophy

AegisOS employs an automated, deterministic deployment pipeline engineered to deliver zero-downtime releases on single-server production infrastructure. The deployment strategy enforces immutable artifacts, zero-downtime Blue-Green stack switching, transactional database migrations, automated pre-flight and post-deployment verification testing, and instant rollback capabilities.

Core deployment principles:
1. **Immutable Build Artifacts**: Application code is compiled into deterministic OCI/Docker container images tagged with git SHA commit hashes. The exact binary image validated in CI/CD and staging is deployed to production without re-compilation.
2. **Zero-Downtime Blue-Green Traffic Swaps**: On single-server infrastructure, two side-by-side production environments (`aegis-blue` and `aegis-green`) alternate active traffic handling via instant Nginx upstream configuration reloads.
3. **Expand-Contract Database Migrations**: Database schema modifications are decoupled from application code releases, ensuring both legacy and newly deployed code versions remain fully compatible during deployment transitions.
4. **Automated Verification & Instant Fallback**: Deployments undergo automated synthetic health probe and smoke test verification before switching live traffic. Any failure triggers automated rollback within < 10 seconds.

---

## 18.2 Deployment Pipeline Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                 AEGISOS CONTINUOUS DEPLOYMENT PIPELINE                            |
|                                                                                                   |
|  1. COMMIT & CI           2. IMAGE BUILD             3. STAGING DEPLOY          4. PROD SWAP      |
|  +-------------------+    +-------------------+      +-------------------+      +---------------+ |
|  | Git Commit (Main) |--->| Docker Multi-Stage|----->| Staging Container |--->| Blue-Green    | |
|  | - Pytest/Jest     |    | - FastAPI & Next.js      | - Integration Test|      | Switch Script | |
|  | - Safety / Snyk   |    | - SBOM Generation |      | - Alembic Check   |      | (Nginx Reload)| |
|  +-------------------+    +-------------------+      +-------------------+      +---------------+ |
|                                                                                     |             |
|                                                                                     v             |
|                                                                             5. POST-DEPLOY VERIFY |
|                                                                             +-------------------+ |
|                                                                             | Smoke Test Suite  | |
|                                                                             | - /healthz        | |
|                                                                             | - /readyz         | |
|                                                                             | - Agent Execution | |
|                                                                             +-------------------+ |
+---------------------------------------------------------------------------------------------------+
```

---

## 18.3 Container Build Process (Multi-Stage Dockerfiles)

AegisOS utilizes multi-stage Docker builds to minimize final image footprint, eliminate build-time compilers from runtime images, and enforce security hardening.

### 18.3.1 FastAPI Backend Multi-Stage `Dockerfile`

```dockerfile
# Stage 1: Build Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PIP_NO_CACHE_DIR=off     PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     libpq-dev     curl     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Runtime Image
FROM python:3.11-slim AS runner

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"     PYTHONUNBUFFERED=1

RUN groupadd -g 10001 aegis &&     useradd -u 10001 -g aegis -s /bin/sh -m aegis &&     apt-get update && apt-get install -y --no-install-recommends     libpq5     curl     && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --chown=aegis:aegis . .

USER aegis:aegis

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3   CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop"]
```

### 18.3.2 Next.js Frontend Multi-Stage `Dockerfile`

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production     PORT=3000     HOST=0.0.0.0

RUN addgroup --system --gid 10001 nodejs &&     adduser --system --uid 10001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3   CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

CMD ["node", "server.js"]
```

---

## 18.4 Database Migration Strategy (Alembic)

Database schema evolution is managed using **Alembic**. To achieve zero downtime during migrations, AegisOS enforces the **Expand-Contract (Parallel Change) Migration Pattern**:

1. **Expand Phase (Pre-Deploy)**: Add new columns as nullable, create new tables, or add non-blocking indexes (`CREATE INDEX CONCURRENTLY`). The running legacy code continues executing unaffected.
2. **Backfill Phase (During Deploy)**: Asynchronously backfill missing data in newly expanded structures.
3. **Contract Phase (Post-Deploy)**: After old application instances are phased out, run a secondary migration adding `NOT NULL` constraints or dropping deprecated columns.

### 18.4.1 Transactional Migration Execution in Pipeline
Migrations are executed strictly prior to routing live traffic to the new Blue/Green stack:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Running Alembic Database Migrations..."
docker exec aegis-backend alembic upgrade head
```

---

## 18.5 Configuration & Secret Management

AegisOS implements a strict configuration hierarchy using Pydantic `BaseSettings`:

```
[Default Hardcoded Fallbacks] -> [Config Files (.env.production)] -> [Environment Variables] -> [Vault Secret Overrides]
```

### 18.5.1 Startup Configuration Validation (`config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, PostgresDsn, RedisDsn

class Settings(BaseSettings):
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "RS256"
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    SENTRY_DSN: HttpUrl | None = None

    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
```

---

## 18.6 Single-Server Blue-Green Deployment Strategy

To execute zero-downtime deployments on a single physical host, AegisOS orchestrates two parallel Docker Compose project stacks (`aegis-blue` and `aegis-green`).

```
+---------------------------------------------------------------------------------------------------+
|                                 SINGLE HOST BLUE-GREEN DEPLOYMENT                                 |
|                                                                                                   |
|                                     +-----------------------+                                     |
|                                     |  Nginx Reverse Proxy  |                                     |
|                                     |  (Active Upstream)    |                                     |
|                                     +-----------------------+                                     |
|                                                 |                                                 |
|                                 Active Traffic  |  (Symlinked Nginx Upstream)                     |
|                                                 v                                                 |
|                      +----------------------------------------------------+                       |
|                      |  ACTIVE STACK: BLUE                                |                       |
|                      |  - Next.js UI (Port 3001)                          |                       |
|                      |  - FastAPI Backend (Port 8001)                      |                       |
|                      +----------------------------------------------------+                       |
|                                                                                                   |
|                                 Deploying Version N+1 (Pre-Traffic)                               |
|                                                 |                                                 |
|                                                 v                                                 |
|                      +----------------------------------------------------+                       |
|                      |  INACTIVE STACK: GREEN                             |                       |
|                      |  - Next.js UI (Port 3002)                          |                       |
|                      |  - FastAPI Backend (Port 8002)                      |                       |
|                      +----------------------------------------------------+                       |
|                                                                                                   |
|                      Both stacks share common stateful services:                                  |
|                      [ PostgreSQL (5432) ]  [ Redis (6379) ]  [ Workspaces ]                         |
+---------------------------------------------------------------------------------------------------+
```

### 18.6.1 Nginx Upstream Switching Script (`switch_traffic.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

TARGET_COLOR="${1}" # "blue" or "green"

CONF_DIR="/etc/nginx/conf.d"
ACTIVE_LINK="${CONF_DIR}/active_upstream.conf"

if [ "${TARGET_COLOR}" == "blue" ]; then
    cat << 'EOF' > "${CONF_DIR}/blue_upstream.conf"
upstream active_backend {
    server aegis-backend-blue:8001;
}
upstream active_frontend {
    server aegis-frontend-blue:3001;
}
EOF
    ln -sf "${CONF_DIR}/blue_upstream.conf" "${ACTIVE_LINK}"
elif [ "${TARGET_COLOR}" == "green" ]; then
    cat << 'EOF' > "${CONF_DIR}/green_upstream.conf"
upstream active_backend {
    server aegis-backend-green:8002;
}
upstream active_frontend {
    server aegis-frontend-green:3002;
}
EOF
    ln -sf "${CONF_DIR}/green_upstream.conf" "${ACTIVE_LINK}"
fi

# Validate Nginx syntax and execute zero-downtime reload
docker exec aegis-nginx nginx -t
docker exec aegis-nginx nginx -s reload
echo "==> Traffic successfully switched to ${TARGET_COLOR} stack."
```

---

## 18.7 Health Checks & Readiness Probes

FastAPI implements distinct `/healthz` (liveness) and `/readyz` (readiness) endpoints to distinguish between process lifecycle state and external service dependency availability.

### 18.7.1 Health & Readiness Implementation (`health.py`)

```python
from fastapi import APIRouter, status, Response
from sqlalchemy import text
from app.db.session import async_session_factory
import redis.asyncio as aioredis
from app.core.config import settings

router = APIRouter()

@router.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness_probe():
    # Liveness probe: verifies process is alive
    return {"status": "alive", "timestamp": time.time()}

@router.get("/readyz")
async def readiness_probe(response: Response):
    # Readiness probe: verifies DB, Redis, and disk storage are operational
    checks = {"database": False, "redis": False}
    
    # Check Database
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        checks["database_error"] = str(e)

    # Check Redis
    try:
        redis = aioredis.from_url(str(settings.REDIS_URL))
        await redis.ping()
        await redis.close()
        checks["redis"] = True
    except Exception as e:
        checks["redis_error"] = str(e)

    all_healthy = all([checks["database"], checks["redis"]])
    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "checks": checks}

    return {"status": "ready", "checks": checks}
```

---

## 18.8 Rollback Procedures

If health checks fail post-deployment or error rates spike, rollback is triggered automatically or executed manually via runbook.

### 18.8.1 Manual Emergency Rollback Runbook
If an operator needs to manually revert traffic back to the prior color stack:

```bash
#!/usr/bin/env bash
set -euo pipefail

CURRENT_STACK=$(cat /var/lib/aegisos/current_stack.txt)

if [ "${CURRENT_STACK}" == "blue" ]; then
    PREVIOUS_STACK="green"
else
    PREVIOUS_STACK="blue"
fi

echo "==> EMERGENCY ROLLBACK: Reverting traffic to ${PREVIOUS_STACK}..."
/opt/aegisos/scripts/switch_traffic.sh "${PREVIOUS_STACK}"
echo "${PREVIOUS_STACK}" > /var/lib/aegisos/current_stack.txt
echo "==> Rollback complete. Inspecting logs on failed ${CURRENT_STACK} stack..."
```

---

## 18.9 Zero-Downtime Deployment Execution Strategy

To achieve zero downtime during deployment:
1. **HTTP Connection Draining**: Nginx `keepalive_timeout 65s` allows active in-flight HTTP requests to finish gracefully.
2. **Worker Task Draining**: Background task workers process active jobs to completion before terminating upon receiving `SIGTERM` signals (`stop_grace_period: 60s`).
3. **Database Non-Blocking Execution**: Migrations lock individual tables for minimal time windows and utilize non-blocking DDL statements.

---

## 18.10 Asset Building & CDN Strategy

Next.js frontend assets are optimized for high-performance global distribution:
* Static HTML pages and JavaScript chunks are pre-compressed during build time using Gzip and Brotli compression algorithms.
* Nginx serves static assets directly from `/app/.next/static` with long-lived immutable cache headers: `Cache-Control: public, max-age=31536000, immutable`.
* Integration with Cloudflare CDN provides edge caching and DDOS defense.

---

## 18.11 SSL/TLS Certificate Management (Let's Encrypt)

Certificates are automatically managed via a dedicated `certbot` container executing ACME v2 HTTP-01 challenges.

### 18.11.1 Automated Renewal Systemd Timer (`/etc/systemd/system/certbot-renew.service`)

```ini
[Unit]
Description=Certbot SSL Certificate Auto-Renewal
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/docker run --rm -v /var/www/certbot:/var/www/certbot -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew --webroot -w /var/www/certbot --quiet
ExecStopPost=/usr/bin/docker exec aegis-nginx nginx -s reload
```

---

## 18.12 Complete Deployment Automation Script (`deploy.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "===================================================="
echo "          AEGISOS AUTOMATED DEPLOYMENT              "
echo "===================================================="

# 1. Determine Target Stack
CURRENT_STACK=$(cat /var/lib/aegisos/current_stack.txt 2>/dev/null || echo "green")
if [ "${CURRENT_STACK}" == "blue" ]; then
    TARGET_STACK="green"
    TARGET_PORT_API="8002"
else
    TARGET_STACK="blue"
    TARGET_PORT_API="8001"
fi

echo "--> Current Stack: ${CURRENT_STACK} | Target Stack: ${TARGET_STACK}"

# 2. Build and Pull Containers
echo "--> Building Docker Images for ${TARGET_STACK}..."
docker compose -f "docker-compose.${TARGET_STACK}.yml" build --parallel

# 3. Database Migrations
echo "--> Running Database Schema Migrations..."
docker compose -f "docker-compose.${TARGET_STACK}.yml" run --rm aegis-backend-builder alembic upgrade head

# 4. Spin Up Target Stack
echo "--> Launching Target Stack (${TARGET_STACK})..."
docker compose -f "docker-compose.${TARGET_STACK}.yml" up -d

# 5. Execute Readiness Health Checks
echo "--> Performing Readiness Verification on Target Stack (Port ${TARGET_PORT_API})..."
RETRIES=12
until [ $RETRIES -le 0 ]; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${TARGET_PORT_API}/readyz" || true)
    if [ "${HTTP_STATUS}" == "200" ]; then
        echo "--> Target Stack Healthy (HTTP 200)!"
        break
    fi
    echo "    Waiting for service readiness... (${RETRIES} retries remaining)"
    sleep 5
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -le 0 ]; then
    echo "[ERROR] Readiness check failed on target stack ${TARGET_STACK}. Aborting deployment!"
    docker compose -f "docker-compose.${TARGET_STACK}.yml" down
    exit 1
fi

# 6. Switch Traffic
echo "--> Switching Active Nginx Upstream Traffic to ${TARGET_STACK}..."
/opt/aegisos/scripts/switch_traffic.sh "${TARGET_STACK}"
echo "${TARGET_STACK}" > /var/lib/aegisos/current_stack.txt

# 7. Teardown Inactive Legacy Stack
echo "--> Stopping Inactive Legacy Stack (${CURRENT_STACK})..."
sleep 10
docker compose -f "docker-compose.${CURRENT_STACK}.yml" down --remove-orphans

echo "===================================================="
echo "   DEPLOYMENT TO ${TARGET_STACK} COMPLETED SUCCESSFULLY!  "
echo "===================================================="
```

---

## 18.13 Post-Deployment Verification (PDV)

Following traffic switch, an automated smoke test suite executes synthetic end-to-end user workflows:

```python
import requests
import sys

BASE_URL = "https://aegis.yourdomain.com"

def run_pdv_tests():
    print("==> Executing Post-Deployment Verification Smoke Tests...")
    
    # Test 1: Liveness Endpoint
    r = requests.get(f"{BASE_URL}/healthz")
    assert r.status_code == 200, "Liveness failed"
    
    # Test 2: Readiness Endpoint
    r = requests.get(f"{BASE_URL}/readyz")
    assert r.status_code == 200, "Readiness failed"
    
    # Test 3: Frontend Home Render
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200, "Frontend render failed"
    
    print("==> ALL POST-DEPLOYMENT SMOKE TESTS PASSED!")

if __name__ == "__main__":
    try:
        run_pdv_tests()
    except Exception as e:
        print(f"[FATAL] Post-deployment verification failed: {e}")
        sys.exit(1)
```

---

## 18.14 Comprehensive Production Deployment Checklist

### Pre-Deployment Checklist
- [ ] All unit, integration, and security tests pass in CI pipeline.
- [ ] Dependency CVE scans (`pip-audit`, `trivy`, `npm audit`) show zero critical or unpatched high vulnerabilities.
- [ ] Database migrations reviewed, tested on staging snapshot, verified zero-downtime compatible.
- [ ] Environment variable changes applied to `.env.production` and secrets manager.
- [ ] Target host disk space verified (> 30 GB available for image builds and logs).
- [ ] Restic offsite database backup verified completed within last 24 hours.

### Deployment Execution Checklist
- [ ] Execution of `deploy.sh` script initiated from clean deployment environment.
- [ ] Multi-stage image build completed successfully with commit SHA tag.
- [ ] Pre-flight Alembic database migrations executed without lock conflicts.
- [ ] Target stack container readiness probes pass (`/readyz` HTTP 200).
- [ ] Zero-downtime Nginx upstream traffic switch executed cleanly (`nginx -s reload`).

### Post-Deployment Verification Checklist
- [ ] Automated smoke test script `smoke_test.py` completes with zero errors.
- [ ] Live error rates in Grafana monitored for 15 minutes; 5xx error rate stays < 0.01%.
- [ ] WebSocket streaming connections verified functioning on UI dashboard.
- [ ] Inactive legacy Blue/Green stack cleanly terminated.
- [ ] Final deployment event logged to Loki and security audit store.\n