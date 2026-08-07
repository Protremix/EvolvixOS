# Verdis Blockchain Integration

EvolvixOS's first managed project is the **Verdis Blockchain** — the world's first fully green, carbon-negative blockchain ecosystem.

## Overview

EvolvixOS manages the Verdis blockchain through:

1. **Health Monitoring** — Real-time JSON-RPC health checks
2. **Ecosystem Tracking** — 7 components monitored
3. **Alert System** — Automated alerts with deduplication
4. **Benchmarking** — RPC latency, block time, validator scoring
5. **Pipeline Templates** — Verdis-specific audit pipeline
6. **AI Agent Context** — Full Verdis knowledge for all agents

## Verdis Ecosystem Components

| Component | Type | Status | Version |
|-----------|------|--------|---------|
| Verdis Chain (Core) | blockchain | Live | spec v11, impl v6 |
| TypeScript SDK | sdk | Ready | 1.0.0 |
| CLI Tool | cli | Ready | 1.0.0 |
| Bridge | bridge | Code ready | 0.1.0 |
| Verdiscan Explorer | explorer | Live | 1.0.0 |
| Android Wallet | wallet | Ready | 1.0.0 |
| Documentation | docs | Ready | 1.0.0 |

## Health Monitoring

```bash
# Run health check
POST /api/v1/verdis-project/health-check

# Get latest snapshot
GET /api/v1/verdis-project/health

# Get health history
GET /api/v1/verdis-project/health/history?limit=100
```

Health metrics tracked:
- Connectivity (RPC reachable)
- Block height
- Peer count
- Syncing status
- Spec/impl version
- Validator count
- RPC method count

## Alerts

Alerts are generated automatically when:
- Chain not reachable (critical)
- Low peer count < 5 (warning)
- Node is syncing (info)
- Low validator count < 10 (warning)
- Outdated spec version < 11 (warning)

```bash
# Get active alerts
GET /api/v1/verdis-project/alerts?resolved=false

# Resolve alert
POST /api/v1/verdis-project/alerts/resolve
{"alert_id": "..."}
```

## Benchmarking

### RPC Latency
```bash
POST /api/v1/verdis-benchmark/rpc-latency?iterations=50
```
Returns: avg, min, max, p50, p95, p99 latency in ms

### Validator Scoring
```bash
POST /api/v1/verdis-benchmark/validator-score
```
Returns: validator count, peer score, overall grade (A-D)

### Block Time
```bash
POST /api/v1/verdis-benchmark/block-time?samples=10
```
Returns: estimated block time, estimated TPS

## Verdis Pipeline Template

The Verdis-specific pipeline template runs a comprehensive audit:

**Constraints:**
- Must pass all 133 workspace tests
- Must build native AND WASM
- Must pass cargo fmt --check
- Must pass cargo clippy
- Must maintain 14 validators
- Must preserve 100B total supply

**Acceptance Criteria:**
- All tests pass (133+)
- Native build succeeds
- WASM build succeeds
- No new clippy warnings
- Code formatted correctly
- Chain produces blocks at ~6s intervals
- GRANDPA finality working

## AI Agent Context

All 11 AI agents receive Verdis-specific context including:
- Consensus mechanism (DPoS + BABE/GRANDPA)
- 13 pallets and their functions
- Token supply (100B VRS/VRDX)
- Eco features (carbon credits, green validators, reforestation)
- Tokenomics (8-category distribution)
- Review guidelines (consensus safety, supply invariants, DPoS logic)

```bash
# Get Verdis context for agents
GET /api/v1/verdis-project/agent-context
```

## Verdis Blockchain Details

| Property | Value |
|----------|-------|
| Consensus | DPoS + BABE/GRANDPA |
| Token | VRS/VRDX |
| Total Supply | 100,000,000,000 |
| Circulating at TGE | 15,000,000,000 (15%) |
| Validators | 14 (DPoS) |
| Block Time | ~6 seconds |
| Pallets | 13 |
| RPC Methods | 121 |
| Domain | verdischain.com |
| Nodes | 18 (2 boot, 2 RPC, 14 validators) |
| Tests | 133 passing |

### Pallets
1. Balances — Token management
2. AmmDex — AMM decentralized exchange
3. CarbonCredits — Carbon credit tracking
4. GreenValidator — Green validator scoring
5. Reforestation — Reforestation logging
6. FungibleTokens — Token standard
7. NFT — Non-fungible tokens
8. Governance — On-chain governance
9. Treasury — Treasury management
10. Council — Council governance
11. Session — Validator sessions
12. Staking — Staking mechanism
13. Sudo — Admin functions
