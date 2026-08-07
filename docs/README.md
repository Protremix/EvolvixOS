# Verdis Ecosystem Documentation

> **Verdis Chain** — The world's first fully green, carbon-negative blockchain | **Token:** VRDX | **SS58:** 909

## Documentation Index

### 📜 Constitution
- [Verdis Ecosystem Constitution](constitution/VERDIS_CONSTITUTION.md) — The governing document for the entire ecosystem

### 🏛️ Governance (Architecture Board)
- [Architecture Board Charter](governance/00-architecture-board-charter.md)
- [Engineering Handbook](governance/01-engineering-handbook.md)
- [Architecture Handbook](governance/02-architecture-handbook.md)
- [Coding Standards](governance/03-coding-standards.md)
- [Security Standards](governance/04-security-standards.md)
- [API Standards](governance/05-api-standards.md)
- [UI/UX Standards](governance/06-ui-ux-standards.md)
- [Infrastructure Standards](governance/07-infrastructure-standards.md)
- [Documentation Standards](governance/08-documentation-standards.md)
- [Release Standards](governance/09-release-standards.md)
- [Review Standards](governance/10-review-standards.md)
- [Testing Standards](governance/11-testing-standards.md)
- [Performance Standards](governance/12-performance-standards.md)
- [Scalability Standards](governance/13-scalability-standards.md)
- [Reliability Standards](governance/14-reliability-standards.md)
- [Incident Response Guide](governance/15-incident-response-guide.md)
- [Engineering Decision Process](governance/16-engineering-decision-process.md)
- [ADR Template](governance/ADR-TEMPLATE.md)
- [Engineering Backlog](governance/engineering-backlog.md)
- [Feature Acceptance Criteria](governance/feature-acceptance-criteria.md)
- [Monthly Review Checklist](governance/monthly-review-checklist.md)

### 📖 Developer Guide
- [Developer Guide](developer-guide/README.md) — Complete developer documentation
- [API Reference](developer-guide/api-reference.md) — SDK API reference for all modules
- [Integration Examples](developer-guide/integration-examples.md) — 7 complete code examples
- [Deployment Guide](developer-guide/deployment.md) — Server deployment and operations

### 🏗️ Architecture
- [Architecture](architecture/ARCHITECTURE.md) — System architecture overview
- [Runtime](architecture/RUNTIME.md) — Runtime specifications (spec v11, 13 pallets)
- [RPC Methods](architecture/RPC.md) — 121 JSON-RPC methods
- [API Architecture](architecture/api_arch.md) — API design document
- [Backend Architecture](architecture/backend_arch.md) — Backend design
- [Frontend Architecture](architecture/frontend_arch.md) — Frontend design

### 🔧 Operations
- [Deployment](operations/DEPLOYMENT.md) — Production deployment guide
- [Operator Guide](operations/OPERATOR_GUIDE.md) — Node operations
- [Monitoring Guide](operations/MONITORING_GUIDE.md) — Prometheus + Grafana monitoring
- [Disaster Recovery](operations/DISASTER_RECOVERY.md) — Backup and recovery procedures
- [Upgrade Guide](operations/UPGRADE_GUIDE.md) — Runtime upgrade procedures
- [Mainnet Readiness](operations/MAINNET_READINESS.md) — Mainnet launch checklist

### 🔑 Validators
- [Validator Guide](validators/VALIDATOR_GUIDE.md) — Validator operations
- [Validator Setup](validators/VALIDATOR_SETUP.md) — Step-by-step validator setup

### 🔍 Explorer
- [Explorer (Verdiscan)](explorer/EXPLORER.md) — Block explorer documentation

### 💰 Wallet
- [Wallet](wallet/WALLET.md) — Wallet documentation

### 🤖 AegisOS Design
- [AegisOS README](aegisos/AegisOS_README.md) — Universal AI Engineering OS overview
- [Vision & PRD](aegisos/design_01_vision_prd.md) — Product requirements
- [System Architecture](aegisos/design_03_system_architecture.md) — Technical architecture
- [UX & Design System](aegisos/design_04_05_ux_design_system.md) — UI/UX specifications
- [AI Organization](aegisos/design_06_ai_organization.md) — AI agent architecture
- [Workflow, Marketplace, Business, Roadmap](aegisos/design_07_08_09_10_workflow_marketplace_business_roadmap.md)
- [Technical Requirements (TRD)](aegisos/doc3_trd.md)
- [Backend Design](aegisos/doc5_backend.md)
- [Frontend Design](aegisos/doc6_frontend.md)
- [API Design](aegisos/doc13_api.md)
- [Design Docs Group 1-5](aegisos/design_docs_group1.md) — Consolidated design documents

### 📊 GPT-4o Review Reports
- [Phase 1 Final Audit](reviews/gpt_phase1_final_audit.md) — 8.5/10, GO
- [Phase 2 Review](reviews/gpt_phase2_review.md) — GO for Phase 2
- [Architecture Board Review](reviews/gpt_architecture_board.md)
- [Bridge Review](reviews/gpt_bridge_review.md) / [V2](reviews/gpt_bridge_review_v2.md)
- [CLI Review](reviews/gpt_cli_review.md)
- [SDK Review](reviews/gpt_sdk_review.md) / [Re-review](reviews/gpt_sdk_rereview.md)
- [Phase 1 Strategy](reviews/gpt_phase1_strategy.md)
- [Phase 1 Architecture](reviews/gpt_phase1_architecture.md)
- [Product Design Rounds 1-8](reviews/gpt_product_design_round1.md) through [Round 8 Final](reviews/gpt_product_design_round8_CORRECTED_FINAL.md)
- [CTO Review Report](reviews/cto_review_report.md)

---

## Chain Specifications

| Property | Value |
|---|---|
| Chain Name | Verdis |
| Token Symbol | VRDX |
| Token Decimals | 18 |
| SS58 Prefix | 909 |
| Total Supply | 100,000,000,000 VRDX (100B) |
| Consensus | BABE + GRANDPA (DPoS) |
| Block Time | ~6 seconds |
| Active Validators | 14 |
| Runtime Version | spec v11, impl v6 |
| RPC Methods | 121 |

## Network Endpoints

| Service | URL |
|---|---|
| HTTP RPC | `https://verdischain.com/rpc` |
| WebSocket RPC | `wss://verdischain.com/ws` |
| Explorer | `https://explorer.verdischain.com` |
| Web Wallet | `https://wallet.verdischain.com` |
| DEX | `https://dex.verdischain.com` |
| Documentation | `https://docs.verdischain.com` |
| Developer Portal | `https://developers.verdischain.com` |

## License

MIT
