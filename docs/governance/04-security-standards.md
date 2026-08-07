# VERDIS GOVERNANCE DOCUMENT 04: SECURITY STANDARDS

**Document ID:** VERDIS-GOV-04  
**Title:** Verdis Ecosystem Zero-Trust Security Standards & Risk Management  
**Version:** 1.0.0  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT GOVERNANCE DOCUMENT  
**Applies To:** All Software Engineers, AI Security Auditors, Sub-Agents, System Administrators, and DevOps Engineers in the Verdis Ecosystem.

---

## TABLE OF CONTENTS
1. [Security Philosophy & Governance Principles](#1-security-philosophy--governance-principles)
   1.1 [Zero-Trust Architecture Model](#11-zero-trust-architecture-model)
   1.2 [Security First Over Feature Speed](#12-security-first-over-feature-speed)
   1.3 [Defense-in-Depth Principle](#13-defense-in-depth-principle)
   1.4 [Principle of Least Privilege](#14-principle-of-least-privilege)
   1.5 [Ecosystem Threat Landscape](#15-ecosystem-threat-landscape)
2. [Blockchain Security Standards](#2-blockchain-security-standards)
   2.1 [Consensus Integrity & DPoS Validator Protection](#21-consensus-integrity--dpos-validator-protection)
   2.2 [Validator Key Management & Hardware Enclaves](#22-validator-key-management--hardware-enclaves)
   2.3 [Substrate RPC Hardening & Call Filters](#23-substrate-rpc-hardening--call-filters)
   2.4 [Pallet & WASM Smart Contract Vulnerability Protections](#24-pallet--wasm-smart-contract-vulnerability-protections)
   2.5 [Substrate Call Filter & Weight Enforcement Code](#25-substrate-call-filter--weight-enforcement-code)
   2.6 [DPoS Slashing & Equivocation Handling](#26-dpos-slashing--equivocation-handling)
3. [Application Security Standards (AegisOS & Portals)](#3-application-security-standards-aegisos--portals)
   3.1 [Authentication Engine: JWT Access & Refresh Tokens](#31-authentication-engine-jwt-access--refresh-tokens)
   3.2 [Password Hashing & Cryptographic Storage](#32-password-hashing--cryptographic-storage)
   3.3 [Role-Based & Attribute-Based Access Control (RBAC/ABAC)](#33-role-based--attribute-based-access-control-rbacabac)
   3.4 [CORS, CSP & Web Vulnerability Defenses (OWASP Top 10)](#34-cors-csp--web-vulnerability-defenses-owasp-top-10)
   3.5 [API Rate Limiting Architecture](#35-api-rate-limiting-architecture)
   3.6 [FastAPI Security Middleware & JWT Verification Code](#36-fastapi-security-middleware--jwt-verification-code)
   3.7 [AES-256-GCM Data Encryption Service](#37-aes-256-gcm-data-encryption-service)
4. [Infrastructure & Network Security](#4-infrastructure--network-security)
   4.1 [Host Firewall Configuration (UFW Rules on `91.98.160.145`)](#41-host-firewall-configuration-ufw-rules-on-9198160145)
   4.2 [SSH Hardening & Key Management](#42-ssh-hardening--key-management)
   4.3 [SSL/TLS Certificate Enforcement & HTTPS Rules](#43-ssltls-certificate-enforcement--https-rules)
   4.4 [Secrets Management & Zero-Leakage Policy](#44-secrets-management--zero-leakage-policy)
   4.5 [Automated Host Hardening Script](#45-automated-host-hardening-script)
   4.6 [Fail2ban & Intrusion Prevention Matrix](#46-fail2ban--intrusion-prevention-matrix)
5. [Vulnerability Management & Incident Response](#5-vulnerability-management--incident-response)
   5.1 [GPT-4o Automated Static Security Reviews](#51-gpt-4o-automated-static-security-reviews)
   5.2 [Dependency Scanning & Automated CVE Tracking](#52-dependency-scanning--automated-cve-tracking)
   5.3 [Incident Response & Security Remediation Protocol](#53-incident-response--security-remediation-protocol)
   5.4 [Standard Incident Audit Report Template](#54-standard-incident-audit-report-template)
6. [Data Protection, Privacy & Encryption](#6-data-protection-privacy--encryption)
   6.1 [Data Classification Standards](#61-data-classification-standards)
   6.2 [Zero On-Chain PII Policy](#62-zero-on-chain-pii-policy)
   6.3 [At-Rest & In-Transit Data Encryption Standards](#63-at-rest--in-transit-data-encryption-standards)
7. [Security Compliance Audit Checklists](#7-security-compliance-audit-checklists)
   7.1 [Blockchain Runtime Security Checklist](#71-blockchain-runtime-security-checklist)
   7.2 [Application & API Security Checklist](#72-application--api-security-checklist)
   7.3 [Infrastructure & Host Security Checklist](#73-infrastructure--host-security-checklist)

---

## 1. SECURITY PHILOSOPHY & GOVERNANCE PRINCIPLES

### 1.1 Zero-Trust Architecture Model
The Verdis Ecosystem operates on a strict **Zero-Trust Security Model**. No entity—whether an external user, an internal microservice, an AI sub-agent, or an RPC peer—is inherently trusted based on network location or implicit context. Every request, API invocation, state modification, or inter-service packet must be explicitly authenticated, authorized, and validated.

### 1.2 Security First Over Feature Speed
Security is non-negotiable. If a conflict arises between delivering a feature quickly and ensuring mathematical/cryptographic safety, security unconditionally takes precedence. No code with known Critical or High severity vulnerabilities can be deployed to production under any circumstances.

### 1.3 Defense-in-Depth Principle
Security controls must be applied in layered defensive rings:
1. **Perimeter Layer:** Network firewalling (UFW), DDoS mitigation, reverse proxy rate-limiting.
2. **Transport Layer:** Mandatory TLS 1.3 encryption for all external and internal RPC/REST paths.
3. **Application Layer:** JWT authentication, RBAC authorization, Pydantic input sanitization.
4. **Data Layer:** AES-256-GCM database encryption, bcrypt password hashing.
5. **Blockchain Layer:** Substrate extrinsic call filters, weight-based fee limits, DPoS consensus validation.

### 1.4 Principle of Least Privilege
Sub-agents, database roles, system users, and service accounts must be provisioned with the absolute minimum set of privileges required to perform their designated function.

### 1.5 Ecosystem Threat Landscape
The Verdis threat model defends against five primary threat vectors:
- **Consensus & Sybil Attacks:** Attempts to compromise the 14 DPoS validator slots or manipulate BABE/GRANDPA block production.
- **Smart Contract Exploits:** Reentrancy, storage bloat, and integer overflow in WASM runtime execution.
- **API & Authentication Attacks:** Credential stuffing, JWT signature forgery, and privilege escalation in AegisOS.
- **Infrastructure Takeover:** SSH brute force, unauthorized RPC administrative access, and container breakout.
- **Data & Secret Leakage:** Accidental commit of private keys, seed phrases, or database credentials.

---

## 2. BLOCKCHAIN SECURITY STANDARDS

```
 +-------------------------------------------------------------------------+
 |                    VERDIS CHAIN SECURITY PARADIGM                       |
 +-------------------------------------------------------------------------+
 | Consensus Engine | BABE (Block Production) + GRANDPA (Finality)         |
 | Validator Slots  | 14 Fixed DPoS Slots with Mandatory Slashing          |
 | Native Token     | VRDX (100 Billion Cap, SS58 Prefix 909)              |
 | Key Cryptography | Sr25519 (Consensus), Ed25519 (GRANDPA), Ecdsa (Bridge)|
 +-------------------------------------------------------------------------+
```

### 2.1 Consensus Integrity & DPoS Validator Protection
Verdis Chain achieves consensus through Delegated Proof-of-Stake (DPoS) with exactly **14 active validator slots**.
- **Slashing Conditions:** Equivocation (double signing) or prolonged offline status results in immediate stake slashing governed by `pallet-dpos-staking`.
- **Equivocation Proofs:** GRANDPA and BABE equivocation proofs are automatically submitted on-chain by monitoring nodes, triggering automated slashing extrinsics without manual intervention.

### 2.2 Validator Key Management & Hardware Enclaves
Validator keys must be stored using secure cryptographic key isolation:
- **Session Keys:** Sr25519 (BABE block production), Ed25519 (GRANDPA finality voting), and Ecdsa (cross-chain bridge operations) must be generated locally inside hardware security modules (HSM) or secure enclave instances.
- **RPC Key Exposure:** The `author_insertKey` and `author_rotateKeys` RPC endpoints must NEVER be exposed over public network interfaces. Access to key insertion endpoints is restricted exclusively to localhost or secure admin sockets.

### 2.3 Substrate RPC Hardening & Call Filters
1. **Safe RPC Methods:** Public node interfaces must run with `--rpc-methods=safe` to disable administrative calls (`author_*`, `system_addReservedPeer`, `system_removeReservedPeer`).
2. **CORS Restrictions:** RPC CORS policy must restrict origin access in production to verified ecosystem domains (`https://verdis.network`, `https://app.verdis.network`).
3. **Transaction Fee Limits:** Anti-spam protection is enforced via `pallet-transaction-payment` weight fees. Transactions with zero weight or invalid signatures are dropped at the transaction pool mempool boundary.

### 2.4 Pallet & WASM Smart Contract Vulnerability Protections
- **Integer Overflow Protection:** All arithmetic operations in Substrate pallets must use checked math (`saturating_add`, `checked_mul`, `saturating_sub`). Direct use of `+` or `-` on balance types is forbidden.
- **Reentrancy Elimination:** WASM smart contracts executing in `pallet-contracts` must follow the Checks-Effects-Interactions pattern. Storage state modifications must occur before external cross-contract calls.

### 2.5 Substrate Call Filter & Weight Enforcement Code

```rust
// blockchain/runtime/src/lib.rs
use frame_support::traits::Contains;
use frame_support::weights::Weight;
use sp_runtime::Perbill;

/// Custom Call Filter enforcing safe transaction boundaries in the runtime.
pub struct ExecutiveCallFilter;

impl Contains<RuntimeCall> for ExecutiveCallFilter {
    fn contains(call: &RuntimeCall) -> bool {
        match call {
            // Block direct execution of internal or administrative pallets by standard users
            RuntimeCall::Sudo(_) => false,
            // Allow standard transfers, staking, and smart contract execution
            RuntimeCall::VrdxToken(_) | 
            RuntimeCall::DposStaking(_) | 
            RuntimeCall::Contracts(_) => true,
            // Default rule: Permit other pallets unless explicitly blacklisted
            _ => true,
        }
    }
}

/// Verifies transaction fee weight limits prior to pool admission
pub fn verify_transaction_weight_limit(weight: Weight) -> bool {
    let max_block_weight = Weight::from_parts(2_000_000_000_000, 0);
    // Disallow single transactions consuming more than 20% of block capacity
    weight.ref_time() <= max_block_weight.ref_time() / 5
}
```

### 2.6 DPoS Slashing & Equivocation Handling
When a validator attempts double signing or equivocation:
1. Monitoring nodes generate an automated equivocation proof payload.
2. The proof is submitted via `submit_unsigned_equivocation_report`.
3. `pallet-dpos-staking` slashes 10% of the validator's bonded VRDX stake.
4. Slashed funds are burned or routed to the ecosystem Treasury pallet.
5. The offending validator is permanently ejected from the active 14-validator set.

---

## 3. APPLICATION SECURITY STANDARDS (AEGISOS & PORTALS)

### 3.1 Authentication Engine: JWT Access & Refresh Tokens
AegisOS utilizes dual-token JSON Web Token (JWT) authentication:
- **Access Tokens:** Signed using `HS256` or `RS256`, short-lived (**15-minute expiration**). Must contain `sub` (User ID), `role`, `iss` (`aegisos`), and `exp`.
- **Refresh Tokens:** Long-lived (**7-day expiration**), stored as encrypted HTTP-only `SameSite=Strict` cookies or securely hashed in the PostgreSQL database.

```
 Client                          AegisOS Auth API                     Database
   |                                    |                                 |
   |-- 1. POST /api/v1/auth/login ---->|                                 |
   |                                    |-- 2. Verify Bcrypt Hash ------->|
   |                                    |<-- Hash Valid ------------------|
   |                                    |                                 |
   |<- 3. Return Access + Refresh Token |                                 |
   |                                    |                                 |
   |-- 4. GET /api/v1/tasks (Bearer) -->|                                 |
   |                                    |-- 5. Validate Signature & Exp --|
   |<- 6. Return Task Data -------------|                                 |
```

### 3.2 Password Hashing & Cryptographic Storage
User credentials and sensitive secret tokens are hashed using `bcrypt` with a minimum work factor of **12 rounds**:

```python
# aegisos/app/core/security.py
import passlib.context
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt

pwd_context = passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET_KEY = "VERDIS_SECRET_CHANGE_IN_PROD"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    # Hashes a raw password string using bcrypt with cost factor 12.
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Verifies a plain password against a stored bcrypt hash.
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = timedelta(minutes=15)) -> str:
    # Generates a signed short-lived JWT access token.
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iss": "aegisos"})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
```

### 3.3 Role-Based & Attribute-Based Access Control (RBAC/ABAC)
AegisOS enforces explicit RBAC across all REST API endpoints:
- **Roles:** `SUPER_ADMIN`, `CTO_ARCHITECT`, `AI_AGENT`, `DEVELOPER`, `READ_ONLY_VIEWER`.
- **Permissions:** Checked via FastAPI dependency injection guards (`require_permission("tasks:write")`).

### 3.4 CORS, CSP & Web Vulnerability Defenses (OWASP Top 10)

| OWASP Vulnerability | Verdis Ecosystem Mitigation Strategy |
| :--- | :--- |
| **A01: Broken Access Control** | Explicit RBAC dependency injection on all FastAPI endpoints; zero unauthenticated routes except `/login`. |
| **A02: Cryptographic Failures** | AES-256-GCM column encryption, bcrypt password hashing (cost 12), TLS 1.3 transport. |
| **A03: Injection (SQL/Command)** | Async SQLAlchemy ORM parameterized queries; Pydantic type coercion; strict input sanitization. |
| **A04: Insecure Design** | Mandatory 9-Step CTO Pipeline architecture review (Step 3) before coding begins. |
| **A05: Security Misconfiguration** | Automated host hardening script; UFW firewall; closed ports; zero default passwords. |
| **A06: Vulnerable Components** | Continuous dependency tracking via `cargo audit`, `pip-audit`, and `npm audit`. |
| **A07: Identification & Auth** | Short-lived JWTs (15 min); Redis rate limiting (100 req/min); account lockout after 5 failures. |
| **A08: Software & Data Integrity** | Cryptographic release signing; Substrate WASM runtime checksum verification. |
| **A09: Logging & Monitoring** | Audit log ingestion in PostgreSQL and Redis Pub/Sub; SSE alert streaming. |
| **A10: SSRF** | Isolated Docker containers; outbound URL validation; blocked internal IP loops. |

### 3.5 API Rate Limiting Architecture
Rate limiting is enforced at the Nginx reverse proxy layer and AegisOS middleware using a Redis sliding-window counter:
- **Default Limit:** 100 requests per minute per IP or Bearer token.
- **Burst Allowance:** Maximum 20 requests burst.
- **Rate Limit Headers:** Returned on every API response (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).

### 3.6 FastAPI Security Middleware & JWT Verification Code

```python
# aegisos/app/api/middleware/security.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis.asyncio as aioredis

class SecurityHeadersAndRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: aioredis.Redis):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        current_minute = int(time.time() // 60)
        rate_key = f"rate_limit:{client_ip}:{current_minute}"

        # 1. Sliding Window Rate Limit check via Redis
        request_count = await self.redis.incr(rate_key)
        if request_count == 1:
            await self.redis.expire(rate_key, 60)

        if request_count > 100:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 100 requests per minute allowed."
            )

        # 2. Process Request
        response = await call_next(request)

        # 3. Inject Mandatory Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self';"
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(max(0, 100 - request_count))

        return response
```

### 3.7 AES-256-GCM Data Encryption Service

```python
# aegisos/app/core/crypto_service.py
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoService:
    def __init__(self, master_key_hex: str):
        self.key = bytes.fromhex(master_key_hex)
        self.aesgcm = AESGCM(self.key)

    def encrypt_data(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return (nonce + ciphertext).hex()

    def decrypt_data(self, encrypted_hex: str) -> str:
        data = bytes.fromhex(encrypted_hex)
        nonce = data[:12]
        ciphertext = data[12:]
        decrypted_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode('utf-8')
```

---

## 4. INFRASTRUCTURE & NETWORK SECURITY

```
 +-------------------------------------------------------------------------+
 |                    HOST FIREWALL & NETWORK SECURITY                     |
 +-------------------------------------------------------------------------+
 | Server Host IP   | 91.98.160.145                                        |
 | Allowed Ports    | 22 (SSH), 80 (HTTP), 443 (HTTPS), 9944 (Substrate RPC)|
 | SSH Rule         | Ed25519 Public Key Only, Password Auth Disabled      |
 | Firewall Engine  | Uncomplicated Firewall (UFW) + Fail2ban Integration  |
 +-------------------------------------------------------------------------+
```

### 4.1 Host Firewall Configuration (UFW Rules on `91.98.160.145`)
The host server operates an active UFW firewall restricting inbound traffic:

```bash
# Production Host UFW Configuration Commands
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH Secure Administration'
sudo ufw allow 80/tcp comment 'HTTP Nginx Web Ingress'
sudo ufw allow 443/tcp comment 'HTTPS Secure Web Ingress'
sudo ufw allow 9944/tcp comment 'Substrate WebSocket JSON-RPC'
sudo ufw enable
```

### 4.2 SSH Hardening & Key Management
- **Key Standard:** SSH access requires Ed25519 public key pairs (`ssh-ed25519`). RSA keys under 4096 bits are rejected.
- **SSH Daemon Settings (`/etc/ssh/sshd_config`):**
  - `PasswordAuthentication no`
  - `PermitRootLogin prohibit-password`
  - `X11Forwarding no`
  - `MaxAuthTries 3`

### 4.3 SSL/TLS Certificate Enforcement & HTTPS Rules
- All external HTTP communication is automatically redirected to HTTPS via Nginx 301 redirects.
- Automated certificate management via Let's Encrypt Certbot with automatic renewal hooks.
- Cipher Suite: Restricted strictly to TLS 1.2 and TLS 1.3 modern ciphers (`ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256`).

### 4.4 Secrets Management & Zero-Leakage Policy
- Secrets (JWT keys, PostgreSQL passwords, validator private seeds, API tokens) must NEVER be hardcoded in source files or checked into git repositories.
- Production secrets are injected into containers via Docker Secrets or secure environment files (`.env`) excluded from source control via `.gitignore`.
- Pre-commit hooks (`gitleaks`) run locally to detect accidental key leakage prior to staging.

### 4.5 Automated Host Hardening Script

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Verdis Host Server Hardening Script ==="

# 1. Configure UFW Firewall
echo "[1/4] Applying UFW rule set..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 9944/tcp
ufw --force enable

# 2. Hardens SSH Configuration
echo "[2/4] Hardening SSH daemon settings..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin yes/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl restart sshd

# 3. Configure Fail2ban
echo "[3/4] Initializing Fail2ban service..."
apt-get update && apt-get install -y fail2ban
systemctl enable fail2ban
systemctl restart fail2ban

# 4. Verify Docker Network Isolation
echo "[4/4] Verifying network bindings..."
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo "=== Host Hardening Complete ==="
```

### 4.6 Fail2ban & Intrusion Prevention Matrix

| Attack Type | Target Service | Fail2ban Filter Rule | Ban Duration |
| :--- | :--- | :--- | :--- |
| **SSH Brute Force** | SSH Daemon (Port 22) | 3 failed attempts in 10 min | 24 Hours |
| **HTTP Flood / DoS** | Nginx (Ports 80/443) | 100 requests / min burst limit | 1 Hour |
| **RPC Exploit Scan** | Substrate (Port 9944) | Invalid RPC method spam | 12 Hours |
| **JWT Brute Force** | AegisOS `/auth/login` | 5 failed logins in 5 min | 2 Hours |

---

## 5. VULNERABILITY MANAGEMENT & INCIDENT RESPONSE

### 5.1 GPT-4o Automated Static Security Reviews
Every task passing through Step 7 of the 9-Step CTO Pipeline undergoes an automated security review performed by GPT-4o. The model evaluates code diffs against a rule matrix covering memory leaks, SQL injection, reentrancy, integer overflow, missing authentication checks, and improper secret exposure.

### 5.2 Dependency Scanning & Automated CVE Tracking
Automated dependency scanning runs continuously across all workspace repositories:
- **Rust Dependencies:** `cargo audit` checks `Cargo.lock` against the RustSec Advisory Database.
- **Python Packages:** `pip-audit` checks `requirements.txt` against PyPI security advisories.
- **Node.js Packages:** `npm audit --audit-level=high` checks JavaScript dependencies.

### 5.3 Incident Response & Security Remediation Protocol

```
[Security Incident Detected]
       |
       v
[Step 1: Immediate Containment]
 - Isolate host/container instance
 - Revoke compromised API keys / JWT tokens
 - Freeze affected Substrate pallet dispatchables via Sudo/Governance
       |
       v
[Step 2: Root Cause Analysis]
 - Extract audit logs from PostgreSQL & systemd journal
 - Reproduce exploit in isolated sandbox environment
       |
       v
[Step 3: GPT-4o Patch Generation]
 - Issue hotfix request through 9-Step CTO Pipeline
 - Verify fix with unit tests & GPT-4o security re-audit
       |
       v
[Step 4: Hotfix Deployment & Signoff]
 - Deploy verified patch to target server (`91.98.160.145`)
 - Post-incident report filed and logged to permanent audit trail
```

### 5.4 Standard Incident Audit Report Template

```markdown
# SECURITY INCIDENT AUDIT REPORT

**Incident ID:** INC-2026-0805-01  
**Severity:** HIGH  
**Component:** AegisOS Authentication Router (`aegisos/app/api/v1/endpoints/auth.py`)  
**Date Reported:** 2026-08-05 09:30:00 UTC  
**Remediation Status:** RESOLVED  

## Executive Summary
An issue was detected in token expiration validation where expired refresh tokens were accepted under specific clock-skew edge cases.

## Root Cause Analysis
The JWT verification function omitted explicit checking of the `nbf` (Not Before) field when evaluating refresh token payloads.

## Remediation Applied
Updated `aegisos/app/core/security.py` to enforce strict `leeway=0` validation on `exp` and `nbf` claims during JWT decoding. Added unit test `test_expired_refresh_token_rejection`.

## CTO Audit Verdict
**APPROVED** by GPT-4o Chief Security Auditor. Zero remaining findings.
```

---

## 6. DATA PROTECTION, PRIVACY & ENCRYPTION

### 6.1 Data Classification Standards
All data within the Verdis Ecosystem is classified into four sensitivity tiers:

| Tier Level | Classification | Examples | Storage Standard | Encryption Required |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Public** | Blockchain blocks, public extrinsic events, OpenAPI docs | On-chain / Public REST | None |
| **Tier 2** | **Internal** | System metrics, build logs, non-sensitive task states | PostgreSQL / Redis | In-transit (TLS) |
| **Tier 3** | **Confidential** | User email, hashed passwords, RBAC permissions | PostgreSQL | At-rest & In-transit |
| **Tier 4** | **Restricted** | Private key seed phrases, JWT secret keys, SSH keys | Vault / Secrets File | AES-256-GCM / Encrypted |

### 6.2 Zero On-Chain PII Policy
Personally Identifiable Information (PII)—including names, email addresses, IP addresses, physical locations, or personal identification numbers—is **STRICTLY PROHIBITED** from being written to the Verdis Chain ledger.
- If user identity must be verified on-chain, only cryptographic zero-knowledge proofs or cryptographic hashes (Blake2b) may be recorded.

### 6.3 At-Rest & In-Transit Data Encryption Standards
- **In-Transit:** TLS 1.3 enforced for all web and WebSocket traffic (`https://`, `wss://`).
- **At-Rest:** Database volumes on host server `91.98.160.145` utilize AES-256 block encryption. Sensitive columns in PostgreSQL use `pgcrypto` for transparent column-level encryption.

---

## 7. SECURITY COMPLIANCE AUDIT CHECKLISTS

### 7.1 Blockchain Runtime Security Checklist
- [ ] Checked arithmetic used across all custom pallet extrinsics.
- [ ] Storage map keys use safe collision-resistant hashing (`Blake2_128Concat`).
- [ ] Safe RPC methods enforced (`--rpc-methods=safe`).
- [ ] `author_*` RPC methods blocked on public interfaces.
- [ ] Weight annotations accurately derived from benchmarking.

### 7.2 Application & API Security Checklist
- [ ] Passwords hashed using `bcrypt` (work factor 12+).
- [ ] JWT access tokens expire in 15 minutes or less.
- [ ] All endpoint inputs validated via Pydantic schemas.
- [ ] Rate limiting active on all API endpoints (100 req/min).
- [ ] CORS origin list explicitly configured without wildcards.

### 7.3 Infrastructure & Host Security Checklist
- [ ] UFW firewall active restricting inbound access to ports `22`, `80`, `443`, `9944`.
- [ ] SSH password authentication disabled; Ed25519 key access only.
- [ ] Fail2ban service running and protecting SSH port.
- [ ] SSL/TLS certificate active with valid Let's Encrypt certificate.
- [ ] Zero hardcoded secrets present in source code repository.

---
*End of Governance Document 04 — Verdis Ecosystem Zero-Trust Security Standards & Risk Management.*
