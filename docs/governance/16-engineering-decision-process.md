# Engineering Decision Process

**Document ID:** GOV-STD-016
**Ratified:** August 5, 2026
**Status:** PERMANENT — Enforced by Architecture Board
**Owner:** GPT-4o (Chief Architect)

---

## 1. Purpose

This document defines how all engineering decisions are made in the Verdis Ecosystem. Every major technical decision must follow this process. No architectural decision may bypass GPT-4o review.

---

## 2. Decision Framework

### 2.1 Decision Pipeline

```
    [Problem Identified]
            │
            ▼
    [Analyze & Define Scope]
            │
            ▼
    [Collect Context]
    (architecture, pallets, tests, deps)
            │
            ▼
    [Identify Options]
    (at least 2 alternatives)
            │
            ▼
    [Evaluate Trade-offs]
    (security, performance, maintainability)
            │
            ▼
    [Write ADR]
    (Architecture Decision Record)
            │
            ▼
    [GPT-4o Review]
            │
    ┌───────┴───────┐
    ▼               ▼
  [Approved]     [Rejected]
    │               │
    ▼               ▼
 [Implement]    [Revise ADR]
 [Test]         [Re-submit]
 [Deploy]
```

### 2.2 Decision Categories

| Category | Examples | Approver | ADR Required |
|----------|----------|----------|-------------|
| Architecture | New pallet, new product, tech stack change | GPT-4o | Yes |
| Security | Auth model, key management, call filters | GPT-4o | Yes |
| Consensus | Block production, finality, validator logic | GPT-4o | Yes |
| Runtime | Spec upgrade, storage migration, pallet config | GPT-4o | Yes |
| API | New RPC methods, REST endpoints, breaking changes | GPT-4o | Yes |
| Infrastructure | Server topology, Docker config, monitoring | GPT-4o | Yes |
| Documentation | Doc structure, whitepaper updates | Implementation Agent | No |
| UI/UX | Component design, color palette, layout | Implementation Agent | No |
| Business | Tokenomics, partnerships, go-to-market | Owner | No (GPT advisory) |
| Brand | Logo, colors, messaging | Owner | No |
| Legal | Compliance, licenses, terms | Owner | No |

---

## 3. ADR (Architecture Decision Record)

### 3.1 When an ADR is Required

An ADR must be created for any decision that:
- Touches consensus, runtime, or cryptography
- Introduces a new technology or dependency
- Changes the API surface (RPC, REST, SDK)
- Modifies the security model
- Alters data schemas or storage layout
- Affects multiple products or phases
- Is difficult to reverse

### 3.2 ADR Format

```
ADR-YYYYMMDD-###

# Title: [Decision Title]

## Status: [Proposed | Accepted | Rejected | Superseded | Deprecated]

## Context
[Why is this decision needed? What problem does it solve?]

## Decision
[What is the decision being made?]

## Alternatives Considered
[What other options were evaluated? Why were they not chosen?]

## Trade-offs
[What are the pros and cons of this decision?]

## Risks
[What could go wrong? What are the failure modes?]

## Consequences
[What impact does this have on the ecosystem?]

## Reasoning
[Why is this the best choice given the current context?]

## Approval
[Approved by: GPT-4o / Owner / Architecture Board]
[Date: YYYY-MM-DD]

## Future Review Criteria
[When should this decision be revisited? What would trigger a re-evaluation?]

## Related ADRs
[List of related ADR IDs]
```

### 3.3 ADR Numbering

- Format: `ADR-YYYYMMDD-###` (e.g., ADR-20260805-001)
- Sequential within each day
- Stored in `governance/adr/` directory

### 3.4 ADR Supersession

- A superseded ADR keeps its original status updated to "Superseded"
- The new ADR explicitly references the old one: "Supersedes ADR-YYYYMMDD-###"
- The old ADR's "Related ADRs" section is updated: "Superseded by ADR-YYYYMMDD-###"

---

## 4. Approval Hierarchy

### 4.1 Technical Decisions

**GPT-4o has final authority on:**
- Architecture correctness
- Security posture
- Performance standards
- Code quality
- Technology selection
- Testing requirements
- Deployment readiness

**Veto Power:**
- GPT-4o can veto any technical decision
- Veto requires written reasoning (saved as ADR amendment)
- No override mechanism for GPT-4o technical veto

### 4.2 Business Decisions

**Owner (Rojs) has final authority on:**
- Tokenomics and token distribution
- Partnerships and collaborations
- Go-to-market strategy
- Brand identity and messaging
- Legal and compliance matters
- Financial decisions
- Irreversible operations (e.g., mainnet launch)

### 4.3 Conflict Resolution

| Conflict Type | Resolution |
|---------------|-----------|
| Technical vs Technical | GPT-4o decides. Final. |
| Business vs Technical | Owner decides on business, GPT-4o on technical impact. |
| Speed vs Quality | GPT-4o decides. Quality always wins per Constitution. |
| Feature vs Security | Security always wins. No exceptions. |

---

## 5. Autonomous Development Rules

### 5.1 What the Agent Does Autonomously

The implementation agent must NOT ask the owner for:
- What to work on next
- How to implement a feature
- Whether to write tests
- Whether to run benchmarks
- Whether to update documentation
- Whether to fix bugs
- Whether to refactor code
- Priority ordering of technical tasks

### 5.2 When to Interrupt the Owner

The agent MUST interrupt the owner ONLY for:

| Trigger | Example |
|---------|---------|
| Business decision | "Should we launch on Polkadot or Ethereum first?" |
| Brand decision | "Should we change the logo color?" |
| Legal decision | "Do we need a license for this technology?" |
| Financial decision | "Should we pay for an external audit?" |
| Credentials | "I need the SSH key to deploy to the server." |
| Manual approval | "Mainnet launch requires your confirmation." |
| Irreversible operation | "This will purge all chain data. Confirm?" |

### 5.3 Backlog Management

The agent maintains a permanent engineering backlog with:
- Tasks scored by business value, engineering value, risk, and effort
- Priority levels P0 (critical) through P3 (nice-to-have)
- Dependencies tracked between tasks
- GPT-4o reprioritizes weekly based on the prioritization formula
- Status tracked: Backlog → In Progress → In Review → Completed → Blocked

---

## 6. Feature Acceptance Criteria

Every feature must satisfy ALL six criteria before implementation:

### Criterion 1: Solves a Real Problem
- Problem statement documented
- Evidence of need (user request, roadmap item, security finding)
- No feature built "because it's interesting"

### Criterion 2: Fits Ecosystem Architecture
- ADR created if architectural impact
- No duplication of existing functionality
- Respects 7-product boundaries
- Follows phase ordering (no skipping)

### Criterion 3: Maintainable
- Code follows coding standards
- Test coverage ≥80%
- Documentation written
- Dependencies minimal and justified

### Criterion 4: Secure
- Security review passed (GPT-4o)
- Zero Critical or High findings
- Input validation on all entry points
- No secrets in code or config

### Criterion 5: Scalable
- Load test results documented
- Capacity analysis performed
- No O(n²) or worse in hot paths
- Horizontal scaling considered

### Criterion 6: Measurable Value
- KPIs defined before implementation
- Success metrics established
- ROI estimated
- Review date scheduled

### 6.1 Veto Power

- **GPT-4o** can veto on technical grounds (architecture, security, performance)
- **Owner** can veto on business grounds (priority, budget, timeline)
- Veto must include written reasoning
- No override for security vetoes

---

## 7. Decision Log

All major decisions are logged in the ADR directory and tracked in the engineering backlog. The decision log provides:

- Audit trail for all architectural choices
- Context for future engineers to understand why decisions were made
- Reference for when decisions should be revisited
- Evidence of governance process compliance

---

## 8. Monthly Architecture Review

On the first Monday of each month, a complete architecture review is performed covering:

1. Blockchain (consensus, finality, pallets, RPC)
2. Applications (wallet, explorer, website, mobile)
3. AI Platform (AegisOS, agents, workflow)
4. Developer Cloud (CI/CD, hosting, storage)
5. Trust Layer (identity, signatures, audit)
6. Marketplace (plugins, agents, templates)
7. Documentation (accuracy, completeness, freshness)
8. Security (vulnerabilities, audits, incidents)
9. Performance (benchmarks, TPS, latency)
10. Technical Debt (code quality, test coverage, deprecated features)
11. Infrastructure (servers, SSL, monitoring, backups)

Output: Recommendations with priority, owner, and deadline. Tracked in engineering backlog.
