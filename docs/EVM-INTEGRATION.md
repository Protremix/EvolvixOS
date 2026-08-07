# Verdis EVM Integration Guide

## Overview

Verdis now supports Ethereum Virtual Machine (EVM) smart contracts, enabling
Ethereum-compatible dApps to deploy on the Verdis blockchain. This is achieved
through Substrate Frontier integration.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Verdis Runtime (Substrate)           │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  BABE    │  │ GRANDPA  │  │   Session/DPoS   │ │
│  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │              EVM Layer (Frontier)             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │pallet-evm│ │pallet-eth│ │pallet-basefee│  │ │
│  │  └──────────┘ └──────────┘ └──────────────┘  │ │
│  └──────────────────────────────────────────────┘ │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Balances │  │ AmmDex   │  │ CarbonCredits   │ │
│  └──────────┘  └──────────┘  └──────────────────┘ │
│                                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │            Verdis-EVM Bridge Pallet            │ │
│  │   (Cross-contract calls: EVM ↔ Substrate)     │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Configuration

### Chain Parameters
- **Chain ID:** 909
- **Gas Currency:** VRDX (Verdis native token)
- **Block Gas Limit:** 30,000,000 (configurable via governance)
- **Min Gas Price:** 1 Gwei (1,000,000,000 Wei)
- **EIP-1559:** Enabled (dynamic base fee)
- **Contract Size Limit:** 24,576 bytes (EIP-170)

### Supported Standards
- ERC-20 (Fungible Tokens)
- ERC-721 (NFTs)
- ERC-1155 (Multi-token)
- ERC-2612 (Permit)
- EIP-1559 (Dynamic fees)
- EIP-170 (Contract size limit)

## Development

### Prerequisites
- Foundry or Hardhat for Solidity development
- MetaMask or Verdis Wallet for deployment
- VRDX for gas

### Deploy a Contract

```bash
# Using Foundry
forge create src/MyToken.sol:MyToken \
  --rpc-url https://verdischain.com/rpc \
  --private-key $VERDIS_PRIVATE_KEY \
  --chain-id 909

# Using Hardhat
npx hardhat run scripts/deploy.js --network verdis
```

### hardhat.config.js

```javascript
module.exports = {
  networks: {
    verdis: {
      url: "https://verdischain.com/rpc",
      chainId: 909,
      accounts: [process.env.VERDIS_PRIVATE_KEY],
      gasPrice: 1000000000, // 1 Gwei
    }
  }
};
```

### MetaMask Configuration
- Network Name: Verdis
- RPC URL: https://verdischain.com/rpc
- Chain ID: 909
- Symbol: VRDX
- Explorer: https://verdischain.com/explorer

## Cross-Chain Integration

EVM contracts can interact with native Substrate pallets via the Verdis-EVM bridge:

| EVM Contract | Substrate Pallet | Direction |
|---|---|---|
| ERC-20 Token | pallet-balances | Bidirectional |
| Carbon Credit | pallet-carbon-credits | Read |
| Green Score | pallet-green-validator | Read |
| AMM Pool | pallet-ammdex | Bidirectional |

## Available Templates

1. **ERC20Token.sol** — Standard fungible token with mint/burn/pause
2. **CarbonCredit.sol** — Carbon credit issuance, tracking, and retirement (ERC-1155)
3. **GreenValidator.sol** — Green validator scoring registry

## Security

- All EVM calls are gas-metered
- Reentrancy guards built into pallet-evm
- Contract size limited to 24KB (EIP-170)
- Storage rent prevents contract bloat
- Verdis governance can pause EVM in emergency

## Gas Costs (Estimated)

| Operation | Gas | VRDX (at 1 Gwei) |
|---|---|---|
| Contract deployment | 1,000,000+ | 0.001+ VRDX |
| ERC-20 transfer | 51,000 | 0.000051 VRDX |
| Contract call | 21,000+ | 0.000021+ VRDX |
| Storage write (32 bytes) | 20,000 | 0.00002 VRDX |

---

*Last updated: August 5, 2026*
