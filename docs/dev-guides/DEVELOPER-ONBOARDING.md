# Verdis Developer Onboarding Guide

## Welcome to Verdis

Verdis is the world's first carbon-negative blockchain ecosystem, built on
Rust + Substrate with DPoS consensus. This guide gets you from zero to deploying
smart contracts in under 30 minutes.

## Prerequisites

- Node.js 18+
- Rust 1.70+ (for native development)
- Git
- A Verdis wallet (download from verdischain.com)
- 10+ VRDX for gas

## 1. Get VRDX Tokens

### Faucet (Testnet)
```bash
curl -X POST https://testnet.verdischain.com/faucet \
  -H "Content-Type: application/json" \
  -d '{"address": "your_wallet_address"}'
```

### Purchase (Mainnet)
Visit verdischain.com/markets to purchase VRDX.

## 2. Set Up Development Environment

```bash
# Clone the repo
git clone https://github.com/Protremix/Verdischain-.git
cd Verdis

# Install dependencies
npm install

# Install EVM tools
npm install solc ethers

# Verify installation
npx solc --version  # Should show 0.8.20+
```

## 3. Verdis Blockchain Overview

### Architecture
```
Verdis Layer-1
├── Consensus: DPoS + BABE/GRANDPA
├── EVM: Full Ethereum compatibility (Chain ID 909)
├── Native Pallets:
│   ├── Balances (VRS/VRDX)
│   ├── AmmDex (AMM DEX)
│   ├── CarbonCredits
│   ├── GreenValidator
│   ├── Reforestation
│   ├── FungibleTokens
│   ├── NFT
│   ├── Governance
│   └── Treasury
└── Smart Contracts (Solidity via EVM)
```

### Key Parameters
| Parameter | Value |
|---|---|
| Chain ID | 909 |
| Total Supply | 100B VRS |
| Consensus | DPoS + BABE/GRANDPA |
| Validators | 101 (14 active) |
| Block Time | ~6 seconds |
| Gas Currency | VRDX |
| Min Gas Price | 1 Gwei |

## 4. Your First Smart Contract

See [EVM Developer Tutorial](./EVM-DEVELOPER-TUTORIAL.md) for full guide.

Quick deploy:
```bash
forge create contracts/templates/ERC20Token.sol:VerdisToken \
  --constructor-args "MyToken" "MTK" 18 1000000000000000000000000 1000000000000000000000000000 \
  --rpc-url https://verdischain.com/rpc \
  --private-key $PRIVATE_KEY \
  --chain-id 909
```

## 5. Use AegisOS

AegisOS is Verdis's AI engineering platform. It manages the Verdis codebase
with 11 AI agents, automated pipelines, and continuous monitoring.

### Access
- Local: http://localhost:3000
- Production: https://aegisos.io (when deployed)

### Key Features
- AI-powered code reviews
- Automated security scanning
- Pipeline analytics
- Knowledge base
- Real-time monitoring
- Multi-project support

## 6. Community

- GitHub: https://github.com/Protremix/Verdischain-
- Explorer: https://verdischain.com/explorer
- Documentation: https://verdischain.com/docs
- Whitepaper: https://verdischain.com/whitepaper

## 7. Eco Features

Verdis is carbon-negative. Every transaction contributes to:
- Carbon credit tracking (on-chain)
- Green validator scoring
- Reforestation logging
- Renewable energy incentives

Deploy carbon credits:
```bash
forge create contracts/templates/CarbonCredit.sol:CarbonCredit \
  --rpc-url https://verdischain.com/rpc \
  --private-key $PRIVATE_KEY
```

---

*Welcome to the greenest blockchain. Build responsibly.*
*Last updated: August 5, 2026*

## Glossary

| Term | Definition |
|---|---|
| **VRS** | Verdis native token (governance) |
| **VRDX** | Verdis gas token (for EVM transactions) |
| **DPoS** | Delegated Proof of Stake — token holders elect validators |
| **BABE** | Blind Assignment for Blockchain Extension — block production |
| **GRANDPA** | GHOST-based Recursive ANcestor-Deriving Prefix Agreement — finality |
| **EVM** | Ethereum Virtual Machine — smart contract execution environment |
| **Pallet** | Substrate module (like a smart contract but native) |
| **RPC** | Remote Procedure Call — how clients talk to the node |
| **Gas** | Unit of computation cost on the EVM |
| **Gwei** | 1 billion Wei (10^-9 VRDX) |
| **AMM** | Automated Market Maker — DEX mechanism |
| **Carbon Credit** | On-chain representation of CO2 offset (1 credit = 1 ton) |
| **Green Score** | Validator eco-rating (0-1000 scale) |
| **AegisOS** | AI engineering platform managing Verdis |
| **Pipeline** | Automated multi-stage workflow (10 stages) |
| **Agent** | AI entity that executes specific task types |
