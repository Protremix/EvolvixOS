# Feature Acceptance Criteria & Evaluation Framework

**Document ID:** GOV-CRITERIA-001  
**Ratified Date:** August 5, 2026  
**Status:** PERMANENT & BINDING  
**Scope:** All Code, Features, Modules, and Services Across the 7 Verdis Products  
**Lead Evaluator:** GPT-4o (Chief Architect & Security Auditor) & Ecosystem Owner  

---

## 1. Executive Summary & Intent

The **Verdis Feature Acceptance Standard** defines the strict, non-negotiable threshold that every proposed feature, enhancement, smart contract, or microservice must satisfy before being merged into production repositories or deployed to production server `91.98.160.145`.

In an autonomous AI-driven engineering environment, clear and enforceable feature acceptance standards prevent code bloat, technical debt accumulation, security vulnerabilities, and ecosystem fragmentation. No code is merged based solely on feature completeness; it must satisfy all **Six Mandatory Feature Acceptance Pillars**.

Every feature submission must demonstrate compliance through concrete verification artifacts, automated test coverage reports, benchmark outputs, and GPT-4o technical sign-offs.

---

## 2. The 6-Point Feature Acceptance Checklist

Every feature proposal and implementation PR must undergo systematic evaluation against the 6 pillars outlined below:

```
+-----------------------------------------------------------------------------------+
|                       THE 6 FEATURE ACCEPTANCE PILLARS                            |
+-----------------------------------------------------------------------------------+
| 1. Solves a Real Problem     | Clear problem statement & verified user/dev need   |
| 2. Ecosystem Architectural Fit| Approved ADR, zero duplication, strictly 7-product |
| 3. Maintainable & Tested     | Unit coverage >=85%, integration >=80%, clean code|
| 4. Zero Vulnerabilities      | GPT-4o security pass, zero Critical/High findings |
| 5. Scalable & Budgeted       | Load test verified, memory/CPU within host budget  |
| 6. Measurable Value          | Defined KPIs, success telemetry hooked into Grafana|
+-----------------------------------------------------------------------------------+
```

---

### Pillar 1: Solves a Real Problem

#### 1.1 Requirements & Mandatory Criteria
- **Problem Statement Mandate:** Every feature submission must include a concrete, written Problem Statement defining the explicit friction, inefficiency, missing capability, or operational bottleneck it resolves.
- **Evidence of Need:** The author must provide clear evidence of need (e.g., developer request, automated audit finding, security vulnerability report, or strategic milestone requirement from `VERDIS_CONSTITUTION.md`).
- **Scope Declaration:** The feature must clearly define its target user persona (dApp developer, validator operator, end-user, AI agent, or ecosystem admin) and explicit non-goals to prevent scope creep.
- **Target Value Statement:** Quantify why solving this problem matters to the ecosystem commercial viability or developer productivity.

#### 1.2 Verification & Checklist Items
- [ ] Written Problem Statement present in PR / proposal description.
- [ ] Demonstrated user/developer need or constitutional milestone mapping.
- [ ] Explicit product boundaries and non-goals defined.
- [ ] Rejection triggered if the feature is speculative ("nice-to-have without clear user benefit").

---

### Pillar 2: Fits Ecosystem Architecture

#### 2.1 Requirements & Mandatory Criteria
- **ADR Mandate:** Features introducing new protocols, state storage layouts, database schemas, public APIs, or dependencies must reference an approved Architecture Decision Record (`governance/ADR-TEMPLATE.md`).
- **Zero Functional Duplication:** In accordance with Constitution Principle 1, the feature must NOT duplicate functionality already provided by existing FRAME pallets, `@verdis/sdk`, `VerdisBridge.sol`, or AegisOS core services.
- **7-Product Boundary Adherence:** The feature must strictly belong to exactly one of the 7 products (Verdis Chain, AegisOS, Applications, Trust Layer, Developer Cloud, Marketplace, Developer Platform) and communicate across product boundaries via standard JSON-RPC or gRPC contracts.
- **Single-Server Compatibility:** Must be deployable on production server `91.98.160.145` within existing container and systemd parameters without breaking co-located validator nodes or web proxies.

#### 2.2 Product Boundary Matrix

| Target Product | Permitted Capabilities & Scopes | Forbidden Cross-Over / Duplications |
| :--- | :--- | :--- |
| **1. Verdis Chain** | Pallets, consensus, WASM contracts, DEX protocols, bridges | UI code, frontend assets, non-blockchain business logic |
| **2. AegisOS** | AI CTO loop, orchestration, prompt engine, vector memory | Direct state mutators bypassing chain RPC |
| **3. Applications** | Web Wallet, Explorer UI, Android/iOS apps, Desktop UI | Duplicated cryptographic primitives (must import SDK) |
| **4. Trust Layer** | Verdis ID, DID specs, release signing, audit log verification | Custom token minting or DEX swap execution |
| **5. Developer Cloud**| Build farm, container launcher, RPC hosting, monitoring | Application UI rendering or direct user auth |
| **6. Marketplace** | Plugin sandbox, AI agent registry, extension monetization | Core runtime consensus modification |
| **7. Developer Platform**| `@verdis/sdk`, `verdis-cli`, REST/GraphQL gateways, docs | Unwrapped raw RPC sockets in application layer |

#### 2.3 Verification & Checklist Items
- [ ] Linked to approved ADR in `governance/adrs/` (or confirmed minor change).
- [ ] Zero code or functional duplication verified via codebase search.
- [ ] Product boundary verified against the Product Boundary Matrix above.
- [ ] Host `91.98.160.145` deployment plan verified.

---

### Pillar 3: Maintainable & High Code Quality

#### 3.1 Requirements & Mandatory Criteria
- **Language & Style Compliance:** Strict adherence to project linting and style rules (`cargo clippy -- -D warnings` for Rust, strict TypeScript without `any`, Android Kotlin coding standards).
- **Mandatory Test Coverage:**
  - **Unit Test Coverage:** >= 85% line coverage across all newly introduced code modules.
  - **Integration Test Coverage:** >= 80% coverage for end-to-end user flows and RPC/API interactions.
- **Error Handling Discipline:** No raw panics (`panic!`, `unwrap()` without safety context), unhandled promise rejections, or generic `catch(e)` blocks. All error paths must return structured error codes and descriptive messages.
- **Documentation Complete:** Inline documentation provided for all public structs, interfaces, functions, and REST/RPC endpoints. Developer guides updated in `docs/`.

#### 3.2 Verification & Checklist Items
- [ ] Cargo clippy / ESLint / Linter executed with zero warnings.
- [ ] Automated coverage report confirms Unit Coverage >= 85%.
- [ ] Automated coverage report confirms Integration Coverage >= 80%.
- [ ] Inline rustdoc / TSDoc / Javadoc comments complete.
- [ ] Developer documentation updated in `docs/`.

---

### Pillar 4: Absolute Security & Vulnerability Free

#### 4.1 Requirements & Mandatory Criteria
- **GPT-4o Security Audit Pass:** All implementation code must pass a comprehensive automated security review by GPT-4o (Chief Security Auditor).
- **Zero Critical / High Findings:** Absolute zero tolerance for Critical or High severity security vulnerabilities (e.g. reentrancy, integer overflow, unchecked key access, SQL injection, XSS, unauthenticated RPC calls, exposed private keys).
- **Static Analysis Clean:** Clean execution outputs from static analysis tools (`cargo-audit`, `npm audit`, `Snyk`, `Bandit`).
- **Cryptographic & Secret Hygiene:** Zero secrets, seed phrases, or private keys written to disk or repository files. Safe key derivation (BIP-39/BIP-44) and AES-256-GCM encryption enforced.

#### 4.2 Security Verification Guidelines
- All seed generation must utilize secure entropy sources (`Bip39Mnemonic.kt`, `KeyManager.kt`).
- Smart contracts must enforce reentrancy guards and checked math operations (`checked_add`, `checked_mul`).
- All RPC endpoints on server `91.98.160.145` must be protected by Nginx rate-limiting or authenticated sessions.

#### 4.3 Verification & Checklist Items
- [ ] GPT-4o Security Review executed with `PASS` status.
- [ ] 0 Critical findings.
- [ ] 0 High findings.
- [ ] Dependency security scan (`cargo audit` / `npm audit`) clean.
- [ ] Key management and secret handling verified compliant.

---

### Pillar 5: Scalable & Resource Budgeted

#### 5.1 Requirements & Mandatory Criteria
- **Benchmarking & Load Test Results:** Quantitative performance benchmark outputs provided proving stability under stress.
- **Substrate Weight Calibration:** Custom FRAME pallet extrinsics must include auto-generated weight benchmarks to calculate deterministic execution fees.
- **Resource Footprint Compliance on Host `91.98.160.145`:**
  - **RAM Overhead:** Feature microservices must operate within pre-approved memory limits (e.g., <250MB for background workers, <1.5GB total AegisOS stack).
  - **CPU Headroom:** Single-core CPU utilization during normal load must not exceed 10%.
  - **RPC Latency SLA:** Node JSON-RPC response times must remain <=50ms under concurrent request load.
- **Capacity Analysis:** Explicit state growth and disk I/O analysis provided for database schemas or blockchain state items.

#### 5.2 Verification & Checklist Items
- [ ] Benchmark test results attached to PR verification report.
- [ ] Substrate extrinsic weights generated (`weights.rs`).
- [ ] Host `91.98.160.145` memory and CPU impact within budget.
- [ ] State growth and disk I/O capacity analysis completed.

---

### Pillar 6: Measurable Value & Telemetry

#### 6.1 Requirements & Mandatory Criteria
- **Defined Key Performance Indicators (KPIs):** Every feature must specify at least two quantitative success KPIs (e.g., "reduces wallet sync time by 40%", "increases DEX swap throughput to 1200 TPS", "lowers error rate to <0.01%").
- **Prometheus Metrics Integration:** Feature backends must expose metric hooks (`/metrics`) formatted for Prometheus scraping on server `91.98.160.145`.
- **Grafana Visualization:** Dashboard panels updated or created in Grafana (`http://91.98.160.145:3000`) to visualize feature operational health and usage volume.
- **Structured Telemetry Logging:** Structured JSON logging emitted for all key state transitions and operational errors.

#### 6.2 Verification & Checklist Items
- [ ] At least 2 quantitative KPIs specified in submission template.
- [ ] Prometheus metrics endpoint implemented and tested.
- [ ] Grafana dashboard configuration updated.
- [ ] Structured JSON logging verified.

---

## 3. Evaluation & Verification Stage Workflow

Every feature follows a four-stage verification process prior to production deployment:

```
+--------------------+      +--------------------+      +--------------------+      +--------------------+
| Stage 1: Proposal  | ---> | Stage 2: Build &   | ---> | Stage 3: GPT-4o    | ---> | Stage 4: Owner     |
| & ADR Sign-Off     |      | Test Execution     |      | Technical Audit    |      | Final Verification |
+--------------------+      +--------------------+      +--------------------+      +--------------------+
```

### 3.1 Detailed Workflow Breakdown

1. **Stage 1 — Proposal & ADR Sign-Off:** Author drafts feature specification detailing problem statement, architectural fit, and KPIs. If architectural changes are required, ADR is submitted and evaluated against Pillar 1 and Pillar 2.
2. **Stage 2 — Implementation & Local Testing:** Autonomous sub-agent or engineer implements code, writes unit/integration tests, and runs local benchmarks. Code must achieve lint clean status and >=85% unit test coverage.
3. **Stage 3 — Autonomous GPT-4o Technical Audit:** GPT-4o runs code review, security audit, and benchmark evaluation against Pillars 3, 4, and 5. If GPT-4o identifies any failing criteria, the PR is automatically marked `REJECTED - REMEDIATION REQUIRED` with line-by-line fix instructions.
4. **Stage 4 — Owner Verification & Production Sign-Off:** GPT-4o submits the verified feature report to the Ecosystem Owner. Ecosystem Owner evaluates business value, licensing, and strategic alignment before issuing final deployment sign-off.

---

## 4. Veto Power Matrix & Technical Governance

To protect ecosystem integrity and prevent technical or business degradation, strict veto rights are assigned:

| Evaluator Role | Veto Scope | Irrideable Veto Conditions | Appeal Path |
| :--- | :--- | :--- | :--- |
| **GPT-4o Chief Architect** | Technical & Security | Security vulnerability (Critical/High), test coverage <85%, architectural duplication, performance SLA breach, host resource overload | Remediation of code defect & re-audit |
| **Ecosystem Owner** | Strategic & Business | Constitutional misalignment, trademark/brand breach, legal risk, unauthorized financial cost, poor UX/DX | Strategic realignment proposal |

### 4.1 GPT-4o Technical Veto
GPT-4o holds absolute, non-overrideable technical veto power over all code submissions. If GPT-4o issues a technical veto due to security flaws, test coverage gaps, or architectural duplication, no implementation agent or human engineer can override the veto without first fixing the underlying code defect.

### 4.2 Ecosystem Owner Strategic Veto
The Ecosystem Owner holds absolute veto power over business, financial, legal, or brand implications. If the Owner rejects a feature on strategic grounds, the decision is final unless appealing via the formal Rejection Appeal Process.

---

## 5. Rejection & Appeal Process

If a feature proposal or pull request is rejected during evaluation, the author must follow the formal 3-step appeal and remediation procedure:

```
+-----------------------------------------------------------------------------------+
|                           REJECTION APPEAL PROCEDURE                              |
+-----------------------------------------------------------------------------------+
| Step 1: Analyze Rejection Report & Categorize Failure (Technical vs Strategic)    |
| Step 2: Formulate Remediation Plan or Architectural Justification                 |
| Step 3: Resubmit Feature Artifacts for GPT-4o & Owner Re-evaluation               |
+-----------------------------------------------------------------------------------+
```

### 5.1 Step-by-Step Appeal Procedure
1. **Analyze Rejection Log:** Review the exact line-by-line feedback and failing pillar IDs provided in the GPT-4o Audit Report or Owner Decision Log.
2. **Remediate Defects:**
   - *Technical Rejections:* Fix security vulnerabilities, add missing unit tests to reach >=85% coverage, refactor code to eliminate duplication, or re-run weight benchmarks.
   - *Strategic Rejections:* Revise feature scope, alter business model, or align user experience with Aegis Design System.
3. **Resubmit Appeal Package:** Submit a formal Appeal Package containing:
   - Updated PR diff and commit hash.
   - Remediation Log explicitly detailing how each failing criterion was resolved.
   - Re-execution benchmark logs and security scan outputs.
4. **Re-Evaluation Timeline:** GPT-4o re-evaluates technical resubmissions within 2 hours of upload. The Ecosystem Owner re-evaluates strategic appeals within 24 hours.

---

## 6. Required Verification Artifacts for Feature Submission

To enable autonomous evaluation by GPT-4o, every feature submission must include the following five concrete verification artifacts attached to the pull request:

1. **Artifact A — Unit & Integration Test Report:** Machine-readable test execution output (e.g. `cargo test` summary, `jest --coverage` report) explicitly demonstrating >=85% unit coverage and >=80% integration coverage.
2. **Artifact B — Static Analysis & Vulnerability Scan Log:** Terminal logs from `cargo audit`, `npm audit`, or `snyk test` confirming zero Critical or High vulnerability alerts.
3. **Artifact C — Performance Benchmark & Weight Log:** Output from Substrate FRAME weight benchmarking harnesses or load-testing scripts proving throughput SLAs and memory usage within server `91.98.160.145` allocations.
4. **Artifact D — Updated Documentation Artifacts:** Markdown documentation diffs in `docs/` reflecting modified RPC methods, CLI flags, configuration parameters, or operator setup steps.
5. **Artifact E — Completed Verification Block:** Signed submission template matching Section 7.

---

## 7. Standard Submission Verification Template

All feature pull requests must include the completed verification block below:

```markdown
## Verdis Feature Submission Verification Block

**Feature Title:** [Feature Name]  
**Target Product:** [1-7 Product Name]  
**Linked ADR:** [ADR-YYYYMMDD-### / N/A]  

### 6-Point Acceptance Checklist Status
- [x] **Pillar 1 (Real Problem):** Problem statement verified; user need documented.
- [x] **Pillar 2 (Architecture Fit):** Zero duplication; fits 7-product boundaries.
- [x] **Pillar 3 (Maintainable):** Unit tests = [XX]%, Integration = [XX]%; Linter clean.
- [x] **Pillar 4 (Secure):** GPT-4o Security Pass = APPROVED; 0 Critical / High findings.
- [x] **Pillar 5 (Scalable):** Benchmarks verified; host 91.98.160.145 memory < [XX] MB.
- [x] **Pillar 6 (Measurable Value):** KPIs defined; Prometheus & Grafana hooked.

**GPT-4o Technical Audit:** APPROVED (`GPT4O-CHIEF-ARCHITECT-APPROVED`)  
**Owner Strategic Sign-Off:** APPROVED (`OWNER-BUSINESS-APPROVED`)  
```

---

## 8. Product-Specific Feature Acceptance Criteria Examples

To illustrate practical application of the 6 Pillars, below are three concrete examples of feature evaluations across different products in the Verdis Ecosystem:

### Example 1: `pallet-dex` Addition to Verdis Chain (Product 1)
- **Pillar 1 (Problem):** Users require decentralized token swap functionality natively on Verdis Chain without relying on third-party bridge hops.
- **Pillar 2 (Architecture):** Approved under `ADR-20260805-001`. Extends `verdis-runtime` via Substrate FRAME v2 pallet; zero duplication of transfer logic.
- **Pillar 3 (Maintainable):** Written in Rust with `#![deny(warnings)]`. Unit test coverage = 92.4%.
- **Pillar 4 (Security):** GPT-4o Security Review Passed; reentrancy checks verified; zero overflow risk using `sp_runtime::Perbill` math.
- **Pillar 5 (Scalable):** Automated Substrate benchmarks executed; weights generated; block execution time overhead = +1.2ms under peak load on server `91.98.160.145`.
- **Pillar 6 (Measurable Value):** KPIs: Swap latency < 6s, Swap volume tracked via Prometheus metric `verdis_dex_swap_volume_total`.

### Example 2: AegisOS AI Code Reviewer Agent (Product 2)
- **Pillar 1 (Problem):** Autonomous developers need automated pull request security auditing before merging code.
- **Pillar 2 (Architecture):** Fits Product 2 (AegisOS); uses AegisOS event bus (`TASK-P2-004`); zero duplication of existing CLI tools.
- **Pillar 3 (Maintainable):** TypeScript microservice with 88.5% unit coverage; zero `any` types.
- **Pillar 4 (Security):** Operates in sandboxed container; secrets injected via AegisOS Secret Manager (`TASK-P2-002`); zero credential exposure.
- **Pillar 5 (Scalable):** Container memory consumption = 180MB RAM on host `91.98.160.145`.
- **Pillar 6 (Measurable Value):** KPIs: Review latency < 45s, Vulnerability catch rate > 98%.

### Example 3: Verdis Web Wallet Transaction Signer (Product 3)
- **Pillar 1 (Problem):** Web users need a secure, browser-based signature prompt for VRDX transfers and WASM smart contract calls.
- **Pillar 2 (Architecture):** Fits Product 3 (Applications); imports `@verdis/sdk` (`ADR-20260805-002`); follows Aegis Design System.
- **Pillar 3 (Maintainable):** React/TypeScript frontend component with 86.0% unit coverage and Cypress integration tests.
- **Pillar 4 (Security):** Seed phrases encrypted in memory using WebCrypto API; key material never transmitted over network.
- **Pillar 5 (Scalable):** Web bundle overhead +45KB; initial rendering time < 100ms.
- **Pillar 6 (Measurable Value):** KPIs: Signing success rate > 99.9%, User signature completion time < 3s.

---

## 9. Enforcement & Audit Log Integrity

- **Automated Verification Pipeline:** Continuous Integration (CI) runners automatically reject any PR that lacks a completed submission verification block or fails code coverage thresholds.
- **Audit Logging:** Every approved feature and its associated verification artifacts (test outputs, benchmark reports, security passes) are recorded in the permanent Verdis Release Audit Log.
- **Retrospective Audits:** During the Monthly Architecture Review (`governance/monthly-review-checklist.md`), GPT-4o audits merged features to verify that production behavior matches the claimed KPIs and resource footprints on host `91.98.160.145`.

### 9.1 Non-Compliance Sanctions & Automatic Rollback
If a deployed feature is subsequently found to violate security rules (Pillar 4) or cause host resource exhaustion on server `91.98.160.145` (Pillar 5):
1. **Immediate Quarantine:** GPT-4o automatically initiates the emergency rollback procedure to restore host state to the previous stable release.
2. **Post-Mortem Analysis:** A `P0` emergency ticket is logged in `engineering-backlog.md` to investigate the root cause and update test harnesses to prevent regression.

---

## 10. Document Revision History

| Version | Date | Author / Entity | Summary of Changes | Ratification Status |
| :--- | :--- | :--- | :--- | :--- |
| **1.0.0** | 2026-08-05 | GPT-4o Chief Architect | Initial ratification of 6-Point Feature Acceptance Criteria | **RATIFIED & EFFECTIVE** |
