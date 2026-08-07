# Review Standards

**Document ID:** GOV-STD-010
**Ratified:** August 5, 2026
**Status:** PERMANENT — Enforced by Architecture Board
**Owner:** GPT-4o (Chief Reviewer)

---

## 1. Purpose

Every code change in the Verdis Ecosystem must pass through the GPT-4o review pipeline before merging or deployment. This document defines the review process, criteria, severity levels, and approval flow.

---

## 2. Review Process

### 2.1 The 9-Step CTO Pipeline

All code follows the mandatory 9-step pipeline:

1. **Analyze** — Understand the task scope and risk
2. **Collect Context** — Gather architecture, pallets, configs, tests, dependencies
3. **Create GPT Request** — Structure the consultation with complete context
4. **GPT Consultation** — GPT-4o provides architecture guidance
5. **Implement** — Build the solution per GPT's guidance
6. **Quality Gates** — Run tests, builds, clippy, fmt, security checks
7. **Technical Report** — Document architecture, files changed, test results
8. **GPT Review** — Submit implementation report to GPT-4o
9. **Iterate** — Fix Critical/High findings, re-submit, repeat until clean

### 2.2 Review Triggers

GPT-4o review is **mandatory** before implementation of any change involving:

| Category | Trigger Examples |
|----------|-----------------|
| Consensus | BABE, GRANDPA, DPoS, session management |
| Runtime | Runtime upgrades, spec version bumps, pallet config |
| Storage | Migrations, storage items, storage weights |
| RPC | New RPC methods, API changes, method removals |
| Networking | P2P, bootnodes, peer discovery |
| Cryptography | Keys, signatures, hashing algorithms |
| Wallet | Key derivation, transaction signing, address encoding |
| Explorer | Data accuracy, RPC queries, API endpoints |
| SDK | API surface, type definitions, breaking changes |
| DEX | Pool math, liquidity, swap logic |
| Token Standards | FungibleTokens, NFTs, transfer logic |
| Governance | Council, Democracy, Treasury, voting |
| Bridges | Cross-chain messages, relayer logic, verification |
| Database | Entity schemas, migrations, data model |
| Deployment | Infrastructure, systemd, Docker, nginx |
| Security | Any security-related change |

---

## 3. Review Criteria

### 3.1 Architecture Correctness (Score: 1-10)

- Does the implementation match the approved architecture?
- Are the correct pallets/modules used?
- Is the data flow correct?
- Are boundaries between products respected?
- Does it follow Substrate/FRAME best practices?

### 3.2 Security (Score: 1-10)

- Input validation on all extrinsics and API endpoints
- Access control (origin checks, privilege escalation prevention)
- Arithmetic safety (checked math, overflow prevention)
- No hardcoded secrets or credentials
- RPC methods don't leak sensitive data
- Call filters prevent unauthorized transactions

### 3.3 Performance (Score: 1-10)

- Weight annotations are accurate
- No unbounded loops in on-chain code
- Storage reads/writes are minimized
- Caching where appropriate
- Benchmark results meet targets

### 3.4 Maintainability (Score: 1-10)

- Code follows naming conventions (Rust snake_case, Python PEP 8, TS camelCase)
- Functions are small and focused (max 50 lines)
- No code duplication
- Dependencies are minimal and justified
- Error handling is comprehensive

### 3.5 Documentation (Score: 1-10)

- All public functions have doc comments (Rustdoc, JSDoc, Python docstrings)
- Architecture decisions recorded in ADRs
- README updated if needed
- API changes documented
- Breaking changes highlighted

### 3.6 Production Readiness (Score: 1-10)

- All tests pass with required coverage
- Both native and WASM builds clean (Rust)
- Clippy and fmt pass (Rust)
- No deprecation warnings
- Deployment guide updated
- Rollback procedure defined

---

## 4. Severity Levels

| Severity | Definition | Action Required |
|----------|-----------|----------------|
| **Critical** | Security vulnerability, data loss risk, consensus break | Must fix immediately. Blocks all deployment. |
| **High** | Major functionality broken, significant performance regression, missing security control | Must fix before merge. Blocks deployment. |
| **Medium** | Minor functionality issue, code quality concern, missing optimization | Fix before next release. Does not block current deployment. |
| **Low** | Cosmetic, style, minor documentation gap | Backlog item. Fix when convenient. |

### 4.1 Iteration Rule

> If GPT-4o identifies any Critical or High findings:
> 1. Fix them immediately
> 2. Re-run all quality gates
> 3. Re-submit for review
> 4. Repeat until zero Critical and zero High findings remain
> 5. Only then mark the task as complete

---

## 5. Approval Flow

```
    [Implementation Complete]
              │
              ▼
    [Quality Gates Pass?]
         │ No ────────► [Fix Issues] ──► [Re-run Gates]
         │ Yes
              ▼
    [Submit to GPT-4o]
    (verdis-cto-review skill)
              │
              ▼
    [GPT-4o Verdict]
         │
    ┌────┴────┐
    ▼         ▼
  [GO]    [NO-GO]
    │         │
    ▼         ▼
 [Merge]  [Fix Critical/High]
 [Deploy] [Re-submit]
           [Repeat]
```

### 5.1 GO Criteria

A GO verdict requires:
- Zero Critical findings
- Zero High findings
- Overall score ≥ 7/10 on all criteria
- All tests passing
- Documentation updated

### 5.2 NO-GO Criteria

A NO-GO is issued when:
- Any Critical finding exists
- Any High finding exists
- Overall score < 6/10 on any criterion
- Tests are failing
- Documentation is missing

---

## 6. Review Documentation

Every review must produce a saved report containing:

1. **Review Date** — When the review was performed
2. **Reviewer** — GPT-4o (always)
3. **Scope** — What was reviewed
4. **Findings** — All findings with severity and details
5. **Scores** — Numeric scores for each criterion
6. **Verdict** — GO or NO-GO
7. **Recommendations** — Specific improvement suggestions
8. **Next Steps** — Required actions before approval

Reviews are saved to the project workspace as `gpt_*_review.md` files.

---

## 7. Weekly Architecture Audit

In addition to per-task reviews, GPT-4o performs a weekly architecture audit using the `verdis-cto-audit` skill covering 11 areas:

1. Blockchain core (consensus, finality, block production)
2. Runtime (pallets, configs, weights)
3. Wallet (security, UX, cross-platform)
4. Explorer (data accuracy, performance)
5. API design (RPC methods, REST endpoints)
6. Developer experience (SDK, docs, examples)
7. Infrastructure (deployment, monitoring, SSL)
8. Security (attack surface, key management)
9. Documentation (whitepaper, developer docs)
10. Performance (TPS, latency, resource usage)
11. Technical debt (code quality, test coverage)

---

## 8. Code Review Checklist

Before submitting to GPT-4o, the implementation agent must verify:

### Rust / Substrate
- [ ] `cargo test --release --workspace` passes
- [ ] `cargo build --release` passes (native + WASM)
- [ ] `cargo fmt --check` passes
- [ ] `cargo clippy` passes (zero warnings)
- [ ] No `unsafe` blocks without justification
- [ ] Weight annotations on all extrinsics
- [ ] No unbounded storage iterations

### Python / FastAPI
- [ ] `pytest` passes with ≥80% coverage
- [ ] `mypy --strict` passes
- [ ] Type hints on all functions
- [ ] No bare `except:` clauses
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured

### TypeScript / React
- [ ] `tsc --noEmit` passes
- [ ] `eslint` passes
- [ ] No `any` types without justification
- [ ] JSDoc on all public exports
- [ ] Error boundaries on all routes

### Infrastructure
- [ ] Dockerfile builds successfully
- [ ] Health check endpoint responds
- [ ] No secrets in config files
- [ ] SSL certificates valid
- [ ] Monitoring targets configured
