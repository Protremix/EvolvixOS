# Verdis Developer FAQ

## General

### What is Verdis?
Verdis is a carbon-negative Layer-1 blockchain built on Rust + Substrate
with DPoS consensus, EVM compatibility, and native eco features
(carbon credits, green validator scoring, reforestation logging).

### What makes Verdis different?
- Carbon-negative: every transaction offsets more CO2 than it produces
- EVM compatible: deploy Ethereum dApps with zero changes
- Native AMM DEX: no need for external DEX
- Green validator scoring: validators rewarded for renewable energy
- 100B fixed supply: no inflation

### What is the chain ID?
909

### What is the gas token?
VRDX (Verdis native token), minimum 1 Gwei per gas.

## Development

### Can I use MetaMask?
Yes. Add a custom network:
- RPC: https://verdischain.com/rpc
- Chain ID: 909
- Symbol: VRDX

### Can I use Hardhat/Foundry?
Yes, both are supported. See [EVM Developer Tutorial](./EVM-DEVELOPER-TUTORIAL.md).

### What Solidity version should I use?
0.8.20+ (matches the EVM pallet version).

### How do I get testnet VRDX?
Use the faucet:
```bash
curl -X POST https://testnet.verdischain.com/faucet \
  -d '{"address": "0x..."}'
```

### What's the max contract size?
24,576 bytes (EIP-170 standard).

### Is EIP-1559 supported?
Yes. Dynamic base fee adjustment is enabled.

## Eco Features

### How do carbon credits work?
1. Verifiers issue credits to addresses (ERC-1155)
2. Credits represent tons of CO2 offset
3. Credits can be retired (burned) to claim the offset
4. Net carbon = total issued - total retired

### What is green validator scoring?
Validators are scored 0-1000 based on:
- 40% renewable energy percentage
- 40% carbon footprint (lower = better)
- 20% uptime percentage

### How does reforestation logging work?
The Reforestation pallet tracks tree planting projects, survival rates,
and carbon sequestration, all verifiable on-chain.

## AegisOS

### What is AegisOS?
An AI engineering platform that manages the Verdis codebase with 11 AI agents,
automated pipelines, knowledge base, and real-time monitoring.

### How do I use AegisOS?
1. Log in at https://aegisos.io (when deployed) or localhost:3000
2. Create or select a project
3. Run a pipeline or create a custom one
4. Monitor results in real-time

### Can I add my own project to AegisOS?
Yes. Use the Multi-Project API:
```bash
POST /api/v1/multi-project/projects
{
  "name": "My Project",
  "type": "web_backend"
}
```

## Security

### Has Verdis been audited?
GPT-4o serves as permanent CTO/Architect/Reviewer. Every change goes through
a 9-step pipeline: analyze → consult GPT → implement → test → report →
GPT review → iterate until clean. Final audit: 8.5/10.

### How are keys handled?
- Keys are stored locally (never on the server)
- All signing is client-side
- No custodial wallets

## Tokenomics

### Total supply?
100,000,000,000 VRS (fixed, no inflation)

### Distribution?
| Category | % |
|---|---|
| Community | 35% |
| Treasury | 20% |
| Team | 15% |
| Investors | 10% |
| Staking | 10% |
| Liquidity | 5% |
| Advisors | 3% |
| Airdrop | 2% |

### Vesting?
- Seed/Private: 60-day vesting
- Public/Final: 30-day vesting
- Protocol-level transfer locks

---

*More questions? Open a discussion on GitHub.*
*Last updated: August 5, 2026*
