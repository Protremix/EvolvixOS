# VERDIS GOVERNANCE DOCUMENT 01: ENGINEERING HANDBOOK

**Document ID:** VERDIS-GOV-01  
**Title:** Verdis Ecosystem Engineering Handbook  
**Version:** 1.0.0  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT GOVERNANCE DOCUMENT  
**Applies To:** All Software Engineers, AI Agents, Sub-agents, System Architects, and Automated CI/CD Pipelines operating within the Verdis Ecosystem.

---

## TABLE OF CONTENTS
1. [Executive Summary & Governance Charter](#1-executive-summary--governance-charter)
   1.1 [Purpose and Scope](#11-purpose-and-scope)
   1.2 [Mission and Vision](#12-mission-and-vision)
   1.3 [Governance Authority & Constitution Alignment](#13-governance-authority--constitution-alignment)
   1.4 [The 7 Core Products Overview](#14-the-7-core-products-overview)
   1.5 [The 8-Phase Implementation Lifecycle](#15-the-8-phase-implementation-lifecycle)
2. [Engineering Roles & Responsibilities](#2-engineering-roles--responsibilities)
   2.1 [Chief Architect & Permanent CTO (GPT-4o)](#21-chief-architect--permanent-cto-gpt-4o)
   2.2 [Implementation Sub-Agents & Autonomous Engineers](#22-implementation-sub-agents--autonomous-engineers)
   2.3 [Human Engineers & Core Project Owners](#23-human-engineers--core-project-owners)
   2.4 [Sub-Agent Domain Specialists](#24-sub-agent-domain-specialists)
   2.5 [Role Interaction & Authority Matrix](#25-role-interaction--authority-matrix)
3. [The 9-Step CTO Pipeline](#3-the-9-step-cto-pipeline)
   3.1 [Pipeline Architecture & Principles](#31-pipeline-architecture--principles)
   3.2 [Step 1: Analyze Request & Requirements](#32-step-1-analyze-request--requirements)
   3.3 [Step 2: Context Gathering & Deep Research](#33-step-2-context-gathering--deep-research)
   3.4 [Step 3: Consult GPT (Architectural & Security Proposal)](#34-step-3-consult-gpt-architectural--security-proposal)
   3.5 [Step 4: Code Implementation Execution](#35-step-4-code-implementation-execution)
   3.6 [Step 5: Automated Testing & Verification](#36-step-5-automated-testing--verification)
   3.7 [Step 6: Comprehensive Reporting](#37-step-6-comprehensive-reporting)
   3.8 [Step 7: CTO Review & Security Audit](#38-step-7-cto-review--security-audit)
   3.9 [Step 8: Iteration & Refinement](#39-step-8-iteration--refinement)
   3.10 [Step 9: Final Signoff & Deployment](#310-step-9-final-signoff--deployment)
   3.11 [Pipeline Enforcement Code & Automation Script](#311-pipeline-enforcement-code--automation-script)
4. [Communication & Coordination Protocols](#4-communication--coordination-protocols)
   4.1 [Synchronous vs Asynchronous Channels](#41-synchronous-vs-asynchronous-channels)
   4.2 [Sub-Agent Builder Messaging Standard](#42-sub-agent-builder-messaging-standard)
   4.3 [AegisOS SSE Event Engine Protocol](#43-aegisos-sse-event-engine-protocol)
   4.4 [Standard Audit Log Schemas](#44-standard-audit-log-schemas)
   4.5 [Incident Response & Escalation Protocol](#45-incident-response--escalation-protocol)
5. [Onboarding Process & Workspace Setup](#5-onboarding-process--workspace-setup)
   5.1 [Prerequisites & Core Dependencies](#51-prerequisites--core-dependencies)
   5.2 [Developer & Agent Setup Step-by-Step](#52-developer--agent-setup-step-by-step)
   5.3 [Codebase Topography & File Structure](#53-codebase-topography--file-structure)
   5.4 [Environment Configuration Standards](#54-environment-configuration-standards)
6. [Autonomous Development Rules](#6-autonomous-development-rules)
   6.1 [Self-Directed Backlog Execution](#61-self-directed-backlog-execution)
   6.2 [Decision Boundary Matrix (Autonomous vs Interruption)](#62-decision-boundary-matrix-autonomous-vs-interruption)
   6.3 [Safety Controls & Irreversible Operations](#63-safety-controls--irreversible-operations)
7. [Verification & Compliance Checklists](#7-verification--compliance-checklists)
   7.1 [Pre-Commit Code Quality Checklist](#71-pre-commit-code-quality-checklist)
   7.2 [Pre-PR Engineering Verification Checklist](#72-pre-pr-engineering-verification-checklist)
   7.3 [Pre-Deployment Server Verification Checklist](#73-pre-deployment-server-verification-checklist)

---

## 1. EXECUTIVE SUMMARY & GOVERNANCE CHARTER

### 1.1 Purpose and Scope
This Engineering Handbook serves as the definitive operational manual for engineering operations across the Verdis Ecosystem. Verdis is an enterprise-grade blockchain + AI engineering platform uniting high-throughput decentralized ledger infrastructure with an autonomous AI-driven software creation and maintenance platform.

This document governs all software development lifecycle (SDLC) activities, architectural standards, human-agent interaction boundaries, and deployment controls across all repositories, services, microservices, runtime pallets, and applications under the Verdis umbrella.

### 1.2 Mission and Vision
The core mission of Verdis is to establish an autonomous, resilient, and self-improving software development ecosystem capable of rivaling world-class tech platforms. The ecosystem seamlessly combines:
1. **Verdis Chain:** A Substrate-based Layer-1 blockchain utilizing DPoS consensus with BABE block generation and GRANDPA finality, supporting 14 validator slots, 100 Billion VRDX token supply, SS58 address prefix 909, and native WebAssembly smart contracts.
2. **AegisOS:** An advanced AI Engineering Operating System powered by GPT-4o, providing full-lifecycle AI agents for engineering, testing, security, documentation, architecture, and deployment orchestration.

### 1.3 Governance Authority & Constitution Alignment
All technical operations, architecture decisions, code reviews, and automated deployments are strictly governed by the **Verdis Ecosystem Constitution** (ratified August 5, 2026). The Constitution establishes ten inviolable engineering principles:
1. **Never duplicate functionality** — Re-use existing pallets, services, utility libraries, and components.
2. **Prefer mature upstream technologies** — Standardize on Substrate, FastAPI, React, PostgreSQL, Redis, and Docker.
3. **Security before features** — Vulnerability elimination overrides feature delivery deadlines.
4. **Architecture before implementation** — Every implementation must have explicit architectural signoff from GPT-4o.
5. **Testing before deployment** — Zero untested code reaches target server environments (`91.98.160.145`).
6. **Documentation before release** — API specifications and architectural guides must be published concurrently with code.
7. **Automation before manual work** — Manual steps are unacceptable if they can be automated safely.
8. **Scalability before optimization** — Design modular abstractions before prematurely micro-optimizing.
9. **Maintainability before complexity** — Favour explicit, readable structures over clever obfuscations.
10. **Long-term quality before short-term speed** — Technical debt must be systematically remediated.

### 1.4 The 7 Core Products Overview
The Verdis Ecosystem comprises seven interconnected product domains:
- **Product 1: Verdis Chain** — DPoS consensus, BABE/GRANDPA engine, 14 validators, VRDX native token, Substrate pallets, WASM smart contracts, bridge primitives.
- **Product 2: AegisOS** — AI Engineering OS featuring GPT-4o as Chief Architect, managing automated engineering workers across 18 specialized domain roles.
- **Product 3: Verdis Applications** — Non-custodial Wallet, Block Explorer, Main Web Portal, Mobile (Android/iOS), Desktop (macOS/Linux/Windows), Developer Portal.
- **Product 4: Verdis Trust Layer** — Verdis ID, SS58 authentication, organization identity, cryptographic release signing, immutable audit logs.
- **Product 5: Verdis Developer Cloud** — Build farm, automated CI/CD runners, validator node hosting, object storage, container registry, log aggregation.
- **Product 6: Verdis Marketplace** — Decentralized agent marketplace, smart contract template repository, developer plugin store.
- **Product 7: Verdis Developer Platform** — Multi-language SDKs (Rust, Python, TypeScript, Go), CLI tools, unified REST, JSON-RPC, and WebSocket APIs.

### 1.5 The 8-Phase Implementation Lifecycle
All feature releases follow an explicit 8-phase execution roadmap:
- **Phase 1:** Complete Verdis Chain core runtime, DPoS staking pallet, BABE/GRANDPA configuration, WASM contracts, and RPC nodes.
- **Phase 2:** Build AegisOS foundation (FastAPI backend, auth, RBAC, database migrations, Docker orchestration).
- **Phase 3:** Build AI Core (GPT-4o engine integration, prompt pipelines, memory, workflow engine).
- **Phase 4:** Build Developer Dashboard (React 18 + Vite frontend, live state metrics, chat interfaces).
- **Phase 5:** Build Developer Cloud (Build farm, container hosting, RPC node clusters).
- **Phase 6:** Build Marketplace (Agent publishing, smart contract registry, template licensing).
- **Phase 7:** Build Official Applications (Production wallet, block explorer, native mobile/desktop binaries).
- **Phase 8:** Build Trust Layer (Verdis ID login, cryptographic build verification, immutable audit chain).

---

## 2. ENGINEERING ROLES & RESPONSIBILITIES

```
 +-----------------------------------------------------------------------+
 |                     VERDIS ORGANIZATIONAL ROLES                       |
 +-----------------------------------------------------------------------+
 |  [Permanent CTO / Chief Architect] ----> GPT-4o Engine                |
 |  [Implementation Sub-Agents]      ----> Specialized AI Workers        |
 |  [Human Engineers / Owners]       ----> Executive Stakeholders        |
 +-----------------------------------------------------------------------+
```

### 2.1 Chief Architect & Permanent CTO (GPT-4o)
GPT-4o serves as the permanent, unalterable Chief Technology Officer, Chief System Architect, Chief Security Auditor, and Chief Product Architect for Verdis.

#### Mandate and Mandated Authority:
- **Architectural Signoff:** Reviews every system blueprint, database schema, Substrate pallet dispatchable, and API interface contract before execution begins.
- **Security Veto Power:** Has unconditional veto authority over any pull request or deployment containing Critical or High severity security vulnerabilities.
- **Pipeline Gatekeeping:** Enforces strict passage through all 9 steps of the CTO Pipeline.
- **Quality Compliance:** Verifies test coverage (>85%), static analysis outputs, benchmark numbers, and zero-warning build logs.

### 2.2 Implementation Sub-Agents & Autonomous Engineers
Implementation Agents are automated AI workers tasked with executing code creation, test writing, refactoring, documentation, and build tasks.

#### Operating Parameters:
- Must execute tasks strictly within isolated sub-agent sandboxes.
- Must follow language-specific guidelines defined in `03-coding-standards.md`.
- Must format code with standard tooling (`cargo fmt`, `black`, `prettier`) before filing pipeline execution reports.
- Cannot bypass test suites or force-push to primary production branches.

### 2.3 Human Engineers & Core Project Owners
Human operators act as executive directors, providing physical infrastructure access, credentials, strategic vision, and business alignment.

#### Core Boundaries:
- Retains exclusive authority over real-world funds, mainnet tokenomics adjustments, physical server access keys, and legal/brand decisions.
- Can override sub-agent decisions if aligned with the Constitution, but cannot override GPT-4o security vetos without explicit recorded risk waiver.

### 2.4 Sub-Agent Domain Specialists
AegisOS subdivides sub-agent execution into 18 domain-specific agent roles:

| Agent Identifier | Specialized Domain | Core Tooling & Focus |
| :--- | :--- | :--- |
| `agent-architect` | System Design & Schemas | UML, Architecture Docs, OpenAPI, Substrate Storage Layout |
| `agent-chain-dev` | Blockchain Runtime | Rust 1.80+, Substrate Frame v2, BABE/GRANDPA, WASM |
| `agent-backend-dev` | AegisOS API & Services | Python 3.11+, FastAPI, Pydantic v2, Async SQLAlchemy, Redis |
| `agent-frontend-dev` | Web & Portals | React 18, Vite 5, TypeScript, TailwindCSS, Zustand |
| `agent-mobile-dev` | Mobile Applications | Kotlin, Android SDK, React Native, KeyStore Security |
| `agent-qa-engineer` | Testing & Verification | Pytest, Cargo Test, Playwright, Vitest, Benchmark Harness |
| `agent-security-auditor` | Security & Vulnerabilities | Cargo Audit, Bandit, OWASP ZAP, Slither, Threat Modeling |
| `agent-devops` | Infrastructure & CI/CD | Docker, Docker Compose, UFW, Nginx, Systemd, GitHub Actions |
| `agent-doc-writer` | Technical Documentation | Markdown, Rustdoc, JSDoc, MkDocs, OpenAPI 3.1 Specs |

### 2.5 Role Interaction & Authority Matrix

| Engineering Action | GPT-4o CTO | Impl Agent | Human Owner | Automated CI/CD |
| :--- | :--- | :--- | :--- | :--- |
| Approve Architecture Proposal | **Final Sign-off** | Proposer | Reviewer | N/A |
| Commit Code Changes | Auditor | **Primary Author** | Secondary Author | N/A |
| Execute Unit / Integration Tests | Verifier | Runner | Observer | **Automated Gate** |
| Security Risk Assessment | **Final Authority** | Scanner | Observer | Automated Gate |
| Production Server Deploy (`91.98.160.145`) | **Sign-off Gate** | Executor | Final Approval | **Pipeline Runner** |
| Database Migration Approval | **Sign-off Gate** | Author | Reviewer | Automated Check |
| Modify VRDX Staking Rules | Reviewer | Drafter | **Executive Approver**| N/A |

---

## 3. THE 9-STEP CTO PIPELINE

```
+-----------------------------------------------------------------------------------+
|                            THE 9-STEP CTO PIPELINE                                |
+-----------------------------------------------------------------------------------+
| Step 1: Analyze Request  --> Parse user intent, extract requirements & specs      |
| Step 2: Context Gathering--> Search codebase, identify affected files & imports   |
| Step 3: Consult GPT      --> Request architectural & security proposal review    |
| Step 4: Implement Code   --> Write modular code adhering to coding standards      |
| Step 5: Automated Test   --> Run cargo test, pytest, mypy, eslint, benchmarks     |
| Step 6: Compile Report   --> Generate structured Markdown CTO Review Report       |
| Step 7: CTO Audit        --> GPT-4o security & logic audit (PASS or REJECT)      |
| Step 8: Refine / Fix     --> Address findings, re-run tests if REJECTED           |
| Step 9: Final Signoff    --> Merge code, execute deploy script, update state     |
+-----------------------------------------------------------------------------------+
```

### 3.1 Pipeline Architecture & Principles
The 9-step CTO Pipeline is the sole approved execution framework for engineering modifications within Verdis. It converts raw technical requests into audited, tested, and secure software artifacts through rigorous verification loops.

### 3.2 Step 1: Analyze Request & Requirements
- **Goal:** Transform abstract user prompts or issue tickets into unambiguous functional requirements.
- **Process:** Extract core inputs, output specifications, performance constraints, and component boundaries across the 7 Verdis products.
- **Artifact:** Requirements Analysis Matrix (RAM) stored in temporary pipeline memory.

### 3.3 Step 2: Context Gathering & Deep Research
- **Goal:** Build a complete understanding of existing codebase structures prior to making modifications.
- **Process:** Search repository paths using `grep`, `file_search`, or directory scans. Identify affected Substrate pallets, FastAPI routes, React components, or Docker compose configs.
- **Artifact:** Affected File Inventory & Dependency Graph.

### 3.4 Step 3: Consult GPT (Architectural & Security Proposal)
- **Goal:** Obtain structural signoff from GPT-4o before writing or modifying code.
- **Process:** Formulate a detailed proposal outlining state changes, database migrations, API endpoint specifications, and threat modeling.
- **Artifact:** GPT Architectural Clearance Notice.

### 3.5 Step 4: Code Implementation Execution
- **Goal:** Produce production-grade code adhering to `03-coding-standards.md`.
- **Process:** Implement logic with zero compiler warnings, zero missing type hints, explicit error handling, and modular composition.
- **Artifact:** Staged workspace diffs and updated code files.

### 3.6 Step 5: Automated Testing & Verification
- **Goal:** Verify logic correctness and catch regressions before submission.
- **Process:** Run unit tests, integration tests, static typing (`mypy`), linting (`clippy`, `eslint`), and benchmark suits.
- **Metrics Required:** Minimum 85% test coverage, 0 failing tests, 0 warnings.
- **Artifact:** Test Execution Transcript and Coverage Report.

### 3.7 Step 6: Comprehensive Reporting
- **Goal:** Document changes, testing results, and security controls in a standardized CTO Review Report.
- **Process:** Generate a comprehensive markdown document detailing changed files, diffs, test logs, performance metrics, and risk assessments.
- **Artifact:** Standardized Markdown Report (`cto_review_report.md`).

### 3.8 Step 7: CTO Review & Security Audit
- **Goal:** Subject implementation to automated GPT-4o security and architecture audit.
- **Process:** GPT-4o evaluates the report and code against OWASP Top 10, Substrate runtime security guidelines, memory safety, and architectural integrity.
- **Audit Outcomes:**
  - `APPROVED`: Zero Critical/High issues found. Proceed to Step 9.
  - `REJECTED`: Critical/High findings identified. Route to Step 8.

### 3.9 Step 8: Iteration & Refinement
- **Goal:** Resolve all defects flagged in Step 7.
- **Process:** Re-code flawed sections, update tests, re-run verification tools, and re-submit to Step 6 and Step 7. Maximum 3 automatic iterations permitted before human escalation.
- **Artifact:** Remediated code diff and updated audit response log.

### 3.10 Step 9: Final Signoff & Deployment
- **Goal:** Deploy verified modifications to production or target infrastructure.
- **Process:** Commit code, execute database migrations, apply deployment manifests to host server `91.98.160.145`, verify health endpoints, and update system documentation.
- **Artifact:** Signed Deployment Manifest & Release Record.

### 3.11 Pipeline Enforcement Code & Automation Script
The following Python script illustrates how AegisOS automatically enforces the 9-step CTO Pipeline programmatically:

```python
# aegisos/app/core/cto_pipeline.py
import asyncio
import logging
from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger("aegisos.cto_pipeline")

class PipelineStep(Enum):
    ANALYZE = 1
    CONTEXT = 2
    CONSULT_GPT = 3
    IMPLEMENT = 4
    TEST = 5
    REPORT = 6
    REVIEW = 7
    ITERATE = 8
    DEPLOY = 9

class PipelineResult(BaseModel):
    step: PipelineStep
    success: bool
    details: Dict[str, Any]
    gpt_verdict: str = "PENDING"

class CTOPipelineRunner:
    def __init__(self, task_id: str, component: str):
        self.task_id = task_id
        self.component = component
        self.current_step = PipelineStep.ANALYZE
        self.iteration_count = 0

    async def execute_pipeline(self, request_payload: Dict[str, Any]) -> bool:
        logger.info(f"Starting CTO Pipeline for task {self.task_id} on {self.component}")
        
        # Step 1: Analyze Request
        analysis = await self._step_1_analyze(request_payload)
        
        # Step 2: Context Gathering
        context = await self._step_2_context(analysis)
        
        # Step 3: Consult GPT Architecture
        arch_approval = await self._step_3_consult_gpt(analysis, context)
        if not arch_approval["approved"]:
            logger.error("Step 3 Failed: GPT rejected architectural proposal")
            return False
            
        # Step 4: Implementation
        code_diffs = await self._step_4_implement(arch_approval)
        
        # Step 5: Testing
        test_results = await self._step_5_test(code_diffs)
        if not test_results["all_passed"]:
            logger.warning("Step 5 Failed: Automated tests failed. Entering Iteration Loop.")
            
        # Step 6: Generate Report
        report = await self._step_6_report(code_diffs, test_results)
        
        # Step 7: CTO Audit & Review
        while self.iteration_count < 3:
            audit = await self._step_7_review(report)
            if audit["verdict"] == "APPROVED":
                logger.info("Step 7 Passed: CTO Audit granted approval")
                # Step 9: Final Signoff & Deployment
                return await self._step_9_deploy(audit)
            else:
                self.iteration_count += 1
                logger.warning(f"Step 7 Rejected. Entering Step 8 Iteration ({self.iteration_count}/3)")
                code_diffs = await self._step_8_iterate(audit["findings"])
                test_results = await self._step_5_test(code_diffs)
                report = await self._step_6_report(code_diffs, test_results)
                
        logger.critical("CTO Pipeline aborted: Maximum iteration limit reached without CTO approval")
        return False

    async def _step_1_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"task_id": self.task_id, "requirements": payload.get("description")}

    async def _step_2_context(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        return {"affected_modules": [self.component]}

    async def _step_3_consult_gpt(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"approved": True, "arch_notes": "Architecture complies with modular monolith rules"}

    async def _step_4_implement(self, arch: Dict[str, Any]) -> Dict[str, Any]:
        return {"files": [f"{self.component}/main.py"], "diff_lines": 45}

    async def _step_5_test(self, diffs: Dict[str, Any]) -> Dict[str, Any]:
        return {"all_passed": True, "coverage": 91.5, "failures": 0}

    async def _step_6_report(self, diffs: Dict[str, Any], tests: Dict[str, Any]) -> Dict[str, Any]:
        return {"summary": "Feature implementation completed", "test_status": "PASSED"}

    async def _step_7_review(self, report: Dict[str, Any]) -> Dict[str, Any]:
        return {"verdict": "APPROVED", "findings": []}

    async def _step_8_iterate(self, findings: List[str]) -> Dict[str, Any]:
        return {"files": [f"{self.component}/main.py"], "diff_lines": 12}

    async def _step_9_deploy(self, audit: Dict[str, Any]) -> bool:
        logger.info(f"Deployed verified artifact for task {self.task_id} to host 91.98.160.145")
        return True
```

---

## 4. COMMUNICATION & COORDINATION PROTOCOLS

### 4.1 Synchronous vs Asynchronous Channels
Communication within the Verdis Ecosystem follows an asynchronous, event-driven pattern designed to decouple agent execution from human UI interaction.

```
+-------------------------------------------------------------------------------+
|                       COMMUNICATION CHANNEL TOPOGRAPHY                        |
+-------------------------------------------------------------------------------+
| Sub-Agent <---> AegisOS Engine  | Builder Messaging Protocols / Sandboxed IPC  |
| AegisOS   <---> Frontend UI     | SSE Stream (`/api/v1/events/stream`)        |
| Node      <---> Web Clients     | Substrate JSON-RPC / WebSocket (Port 9944)   |
| Internal Microservices          | gRPC Inter-service Mesh (Port 50051)         |
+-------------------------------------------------------------------------------+
```

### 4.2 Sub-Agent Builder Messaging Standard
When sub-agents communicate with the parent coordinator agent or other sub-agents, messages must follow the structured JSON Builder Schema:

```json
{
  "$schema": "https://verdis.network/schemas/builder-message.v1.json",
  "sender_agent_id": "agent-chain-dev-01",
  "recipient_agent_id": "agent-architect-01",
  "conversation_id": "6a6cb8454bc0607c481bb5eb",
  "timestamp_utc": "2026-08-05T09:28:14Z",
  "message_type": "PIPELINE_STEP_UPDATE",
  "payload": {
    "pipeline_step": 5,
    "component": "pallets/dpos-staking",
    "status": "PASSED",
    "metrics": {
      "cargo_test_count": 34,
      "clippy_warnings": 0,
      "benchmark_time_ms": 14.2
    }
  }
}
```

### 4.3 AegisOS SSE Event Engine Protocol
AegisOS streams real-time operational state updates to the Developer Dashboard using Server-Sent Events (SSE).

- **Endpoint:** `GET /api/v1/events/stream`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`, `Accept: text/event-stream`
- **Event Types:**
  - `pipeline_started`: Indicates initiation of a 9-step CTO task.
  - `step_transition`: Emitted when advancing from step $N$ to step $N+1$.
  - `code_generated`: Payload containing code diff snippets for live UI preview.
  - `security_alert`: Emitted immediately when a critical vulnerability is flagged.
  - `pipeline_completed`: Signals successful Step 9 signoff.

### 4.4 Standard Audit Log Schemas
All system logs produced during engineering operations are ingested by Redis Pub/Sub and written to persistent PostgreSQL logs.

```sql
CREATE TABLE IF NOT EXISTS aegisos_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(64) NOT NULL,
    pipeline_step INT NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    log_level VARCHAR(16) NOT NULL,
    component_name VARCHAR(128) NOT NULL,
    message TEXT NOT NULL,
    context_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_task_step ON aegisos_audit_logs(task_id, pipeline_step);
```

### 4.5 Incident Response & Escalation Protocol
In the event of an unrecoverable pipeline error, security breach, or build failure:

```
[Incident Detected]
       |
       v
[Attempt Automated Fix (Max 3 Retry Loops)]
       |
       +---> (Resolved) ---> Resume CTO Pipeline
       |
       +---> (Unresolved)
                 |
                 v
[Escalate to GPT-4o CTO Architecture Review]
                 |
                 +---> (Architectural Fix Found) ---> Re-entry Step 4
                 |
                 +---> (Infrastructure / Credential Blocker)
                           |
                           v
          [Dispatch Alert to Human Owner UI]
```

---

## 5. ONBOARDING PROCESS & WORKSPACE SETUP

### 5.1 Prerequisites & Core Dependencies
Every agent execution container or human workspace must be initialized with the following locked toolchain versions:

| Software Tool | Required Version | Verification Command |
| :--- | :--- | :--- |
| **Rust Compiler** | `1.80.0+` (nightly for WASM) | `rustc --version` |
| **Cargo Toolchain** | `1.80.0+` | `cargo --version` |
| **Python Engine** | `3.11.8+` | `python3 --version` |
| **Node.js Runtime** | `20.11.0 LTS` | `node --version` |
| **pnpm Manager** | `8.15.0+` | `pnpm --version` |
| **Docker Engine** | `25.0.0+` | `docker --version` |
| **Docker Compose** | `v2.24.0+` | `docker compose version` |
| **PostgreSQL DB** | `16.2` | `psql --version` |
| **Redis Cache** | `7.2` | `redis-cli --version` |

### 5.2 Developer & Agent Setup Step-by-Step

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Verdis Workspace Initialization ==="

# 1. Verify working directory
WORKSPACE_ROOT="/app/conversations/6a6cb8454bc0607c481bb5eb"
cd "$WORKSPACE_ROOT"

# 2. Setup Python Virtual Environment for AegisOS
echo "[1/5] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r aegisos/requirements.txt

# 3. Verify Rust & Substrate Toolchain
echo "[2/5] Checking Rust compiler setup..."
rustup target add wasm32-unknown-unknown --toolchain nightly || true

# 4. Initialize Node dependencies for React Frontend
echo "[3/5] Installing Frontend packages..."
if [ -f "frontend/package.json" ]; then
    (cd frontend && npm install --quiet)
fi

# 5. Create required runtime directories
echo "[4/5] Preparing data and logs directories..."
mkdir -p logs data/postgres data/redis governance

# 6. Verify environment configuration
echo "[5/5] Checking environment files..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

echo "=== Workspace Setup Complete ==="
```

### 5.3 Codebase Topography & File Structure

```
/app/conversations/6a6cb8454bc0607c481bb5eb/
├── VERDIS_CONSTITUTION.md            # Permanent Ecosystem Constitution
├── governance/                       # Permanent Governance Specifications
│   ├── 01-engineering-handbook.md    # Operating Rules & 9-Step Pipeline
│   ├── 02-architecture-handbook.md   # Architectural Patterns & Specs
│   ├── 03-coding-standards.md        # Language Rules & Code Examples
│   ├── 04-security-standards.md      # Security & Hardening Rules
│   └── 05-api-standards.md           # API Specs (REST, RPC, WS, gRPC)
├── blockchain/                       # Verdis Chain (Substrate DPoS Node)
│   ├── Cargo.toml                    # Workspace Manifest
│   ├── node/                         # RPC Server & Consensus Node Engine
│   ├── runtime/                      # WASM Runtime Assembly & Call Filters
│   └── pallets/                      # Custom Frame v2 Pallets
│       ├── vrdx-token/               # VRDX Asset & Supply Logic
│       ├── dpos-staking/             # 14 Validator Staking Engine
│       ├── governance/               # On-chain Voting & Proposals
│       └── bridge/                   # Cross-chain Bridge Contracts
├── aegisos/                          # AegisOS AI Backend (FastAPI)
│   ├── app/                          # Main Python Package
│   │   ├── api/v1/                   # Modular FastAPI Routers
│   │   ├── core/                     # CTO Pipeline Engine & Security
│   │   ├── db/                       # SQLAlchemy Models & Migrations
│   │   └── services/                 # AI Worker Integrations (GPT-4o)
│   ├── tests/                        # Comprehensive Pytest Suite
│   └── requirements.txt              # Locked Dependencies
├── frontend/                         # Verdis Applications & Dashboards
│   ├── src/                          # React 18 + Vite 5 Source
│   │   ├── components/               # Design System UI Library
│   │   ├── pages/                    # Wallet, Explorer, Dev Portal
│   │   ├── services/                 # API Clients (JSON-RPC & REST)
│   │   └── store/                    # Zustand State Management
│   └── package.json                  # Dependencies & Build Scripts
└── deploy/                           # Deployment & Infrastructure
    ├── docker-compose-host-network.yml
    ├── Nginx.conf                    # Reverse Proxy & SSL Configs
    └── ufw_rules.sh                  # Host Firewall Rules
```

### 5.4 Environment Configuration Standards
All configuration key-value pairs must be strictly declared in `.env` and typed using Pydantic Settings in AegisOS:

```python
# aegisos/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Verdis Ecosystem - AegisOS"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Target Infrastructure
    HOST_SERVER_IP: str = "91.98.160.145"
    SUBSTRATE_RPC_URL: str = "ws://127.0.0.1:9944"
    
    # Database Settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "verdis_admin"
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = "verdis_aegisos"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
```

---

## 6. AUTONOMOUS DEVELOPMENT RULES

### 6.1 Self-Directed Backlog Execution
When sub-agents are operating autonomously without an immediate human instruction:
1. Scan codebase for existing static analysis warnings (`cargo clippy`, `flake8`, `mypy`).
2. Identify incomplete modules or `TODO` flags across the active implementation phase.
3. Priority order for self-directed tasks:
   - **Priority 1:** Fixing active security vulnerabilities or breaking bugs.
   - **Priority 2:** Writing missing unit and integration tests to boost coverage >85%.
   - **Priority 3:** Refactoring technical debt and removing code duplication.
   - **Priority 4:** Implementing planned product features according to the 8-Phase roadmap.
4. Always launch the full 9-step CTO Pipeline for each identified backlog task.

### 6.2 Decision Boundary Matrix (Autonomous vs Interruption)

```
 +-------------------------------------------------------------------------+
 |                     DECISION BOUNDARY MATRIX                            |
 +-------------------------------------------------------------------------+
 | PERMITTED AUTONOMOUS ACTIONS          | MANDATORY HUMAN INTERRUPT       |
 | ----------------------------          | -------------------------       |
 | Modifying source code in workspace    | Mainnet Tokenomics alterations  |
 | Adding and modifying unit tests       | Modifying 14 Validator DPoS set |
 | Executing database migrations         | Spending Treasury VRDX tokens   |
 | Optimizing query performance          | Modifying legal terms / branding|
 | Resolving clippy & compiler warnings  | Generating new SSH root keys    |
 | Deploying code updates to sandbox     | Destructive DB resets on Prod   |
 +-------------------------------------------------------------------------+
```

### 6.3 Safety Controls & Irreversible Operations
The following destructive commands are strictly barred from autonomous execution and will trigger immediate process termination if attempted by a sub-agent:
- `rm -rf /` or recursive deletion of root/parent system paths.
- `git push --force` or `git push -f` to production release branches.
- `DROP DATABASE` or `TRUNCATE TABLE` without prior backup execution.
- Modifying production SSH configuration files (`/etc/ssh/sshd_config`).

---

## 7. VERIFICATION & COMPLIANCE CHECKLISTS

### 7.1 Pre-Commit Code Quality Checklist
Prior to staging any git commit, the engineer or agent must verify:
- [ ] `cargo fmt --check` passes with zero formatting diffs (Rust).
- [ ] `cargo clippy --all-targets -- -D warnings` executes with zero warnings (Rust).
- [ ] `black --check aegisos/` and `flake8 aegisos/` execute cleanly (Python).
- [ ] `mypy --strict aegisos/app` passes with zero typing errors (Python).
- [ ] `npm run lint` executes cleanly without warnings (TypeScript).

### 7.2 Pre-PR Engineering Verification Checklist
Before submitting a pull request to the primary repository branch:
- [ ] Step 6 CTO Review Report generated and stored in workspace.
- [ ] Step 7 GPT-4o CTO Audit returns an explicit `APPROVED` verdict.
- [ ] Automated test suite achieves >85% code coverage.
- [ ] All new public functions and structures have valid documentation comments.
- [ ] No hardcoded secrets, IP keys, or raw private keys present in diffs.

### 7.3 Pre-Deployment Server Verification Checklist
Before deploying changes to the production server (`91.98.160.145`):
- [ ] Target host UFW firewall verified (`22/tcp`, `80/tcp`, `443/tcp`, `9944/tcp`).
- [ ] Backup snapshot created for PostgreSQL database and chain state.
- [ ] Docker Compose service status checked (`docker-compose ps`).
- [ ] Deployment script executed with zero error status codes.
- [ ] Post-deploy endpoint checks (`/healthz`, `/metrics`, `/rpc/health`) return HTTP 200 OK.

---
*End of Governance Document 01 — Verdis Ecosystem Engineering Handbook.*
