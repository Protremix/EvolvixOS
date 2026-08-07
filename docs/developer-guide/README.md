# Verdis Blockchain — Developer Documentation

> **Version:** 1.0.0 | **Chain:** Verdis | **Token:** VRDX (18 decimals) | **SS58:** 909 | **Consensus:** BABE/GRANDPA (DPoS)

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Network Endpoints](#network-endpoints)
4. [SDK (TypeScript)](#sdk-typescript)
5. [CLI Tool](#cli-tool)
6. [Cross-Chain Bridge](#cross-chain-bridge)
7. [RPC Methods](#rpc-methods)
8. [Pallets & Runtime](#pallets--runtime)
9. [Smart Contracts](#smart-contracts)
10. [DEX (AMM)](#dex-amm)
11. [Eco Protocol](#eco-protocol)
12. [Staking (DPoS)](#staking-dpos)
13. [Tokenomics](#tokenomics)
14. [Security](#security)
15. [Examples](#examples)

---

## Overview

Verdis is the world's first fully green, carbon-negative blockchain built on Rust + Substrate. It features:

- **BABE/GRANDPA consensus** with DPoS validator selection (14 active validators)
- **Native AMM DEX** with 6 liquidity pools
- **Eco protocol** with carbon credit tracking, reforestation logging, and green validator scoring
- **Smart contracts** via pallet-contracts (WASM-based)
- **Token standards** (FungibleTokens, NFTs)
- **Governance** (Council, Democracy, Treasury)
- **Cross-chain bridge** to Ethereum and Polkadot

**Chain Specifications:**
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

---

## Quick Start

### Install the SDK

```bash
npm install @verdis/sdk
# or
yarn add @verdis/sdk
```

### Connect to the Network

```typescript
import { VerdisClient } from '@verdis/sdk';

const client = new VerdisClient({
  endpoint: 'wss://verdischain.com/ws',
});

await client.connect();

// Get chain state
const state = await client.getChainState();
console.log(`Block #${state.latestBlockNumber} | Validators: ${state.activeValidators}`);
```

### Create an Account

```typescript
import { generateMnemonic, createKeypair } from '@verdis/sdk';

const mnemonic = generateMnemonic();
const keypair = createKeypair(mnemonic, { name: 'My Account' });

console.log('Address:', keypair.address);
console.log('Mnemonic:', mnemonic); // Save securely!
```

### Check Balance

```typescript
const balance = await client.getBalance(keypair.address);
console.log(`Free: ${balance.free} Planck`);
console.log(`Reserved: ${balance.reserved} Planck`);
```

### Transfer VRDX

```typescript
const result = await client.keys.signAndSubmit(
  client.api,
  client.tx.transfer('5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty', '1000000000000000000'),
  keypair
);
console.log('Tx:', result.txHash);
```

---

## Network Endpoints

| Service | URL |
|---|---|
| WebSocket RPC | `wss://verdischain.com/ws` |
| HTTP RPC | `https://verdischain.com/rpc` |
| Explorer (Verdiscan) | `https://explorer.verdischain.com` |
| Web Wallet | `https://wallet.verdischain.com` |
| DEX Interface | `https://dex.verdischain.com` |
| Validator Dashboard | `https://validators.verdischain.com` |
| Documentation | `https://docs.verdischain.com` |
| Developer Portal | `https://developers.verdischain.com` |
| API | `https://api.verdischain.com` |
| Faucet | `https://faucet.verdischain.com` |
| Status/Monitoring | `https://status.verdischain.com` |

---

## SDK (TypeScript)

### Installation

```bash
npm install @verdis/sdk
```

### Modules

| Module | Description |
|---|---|
| `core` | VerdisClient, chain queries, transaction submission |
| `keyring` | Key management, mnemonic generation, SS58 encoding |
| `modules/staking` | DPoS staking (delegate, undelegate, epoch info) |
| `modules/dex` | AMM DEX (pools, swap, add liquidity, prices) |
| `modules/eco` | Carbon credits, reforestation projects, green scores |
| `modules/contracts` | Smart contract calls and execution |
| `modules/tokens` | Fungible tokens and NFTs |

### Key API Reference

#### `VerdisClient`

```typescript
class VerdisClient {
  constructor(options: { endpoint: string; autoConnect?: boolean })
  connect(): Promise<void>
  disconnect(): Promise<void>
  getChainState(): Promise<ChainState>
  getBalance(address: string): Promise<BalanceInfo>
  api: ApiPromise       // Direct @polkadot/api access
  keys: VerdisKeyring    // Key management
  chain: ChainQueries    // Block queries
  system: SystemQueries  // Health, peers
  tx: TransactionBuilder // Transfer, custom extrinsics
}
```

#### `StakingApi`

```typescript
class StakingApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)
  getActiveValidators(): Promise<string[]>
  getCurrentEpoch(): Promise<EpochInfo>
  delegate(account: KeyringPair, validator: string, amount: string): Promise<TxResult>
  undelegate(account: KeyringPair, validator: string): Promise<TxResult>
}
```

#### `DexApi`

```typescript
class DexApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)
  getAllPools(): Promise<PoolInfo[]>
  getPool(poolId: number): Promise<PoolInfo>
  getPrice(assetIn: string, assetOut: string): Promise<PriceInfo>
  swap(account: KeyringPair, assetIn: string, assetOut: string, amountIn: string, minOut: string): Promise<TxResult>
  addLiquidity(account: KeyringPair, assetA: string, assetB: string, amountA: string, amountB: string): Promise<TxResult>
}
```

#### `EcoApi`

```typescript
class EcoApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)
  getCarbonCredits(address: string): Promise<string>
  getReforestationProjects(): Promise<ProjectInfo[]>
  getGreenScore(validator: string): Promise<number | null>
  mintCarbonCredits(account: KeyringPair, amount: string, proof: string): Promise<TxResult>
}
```

#### `ContractsApi`

```typescript
class ContractsApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)
  call(address: string, method: string, args?: any[]): Promise<ContractResult>
  execute(account: KeyringPair, address: string, method: string, args?: any[], value?: string): Promise<TxResult>
  getCodeHash(address: string): Promise<string | null>
}
```

### Integration Examples

See the `integration-examples/` directory for complete working examples:
- `query-chain.ts` — Basic chain queries
- `create-wallet.ts` — Account creation and balance check
- `transfer-vrdx.ts` — Token transfer
- `delegate-stake.ts` — DPoS delegation
- `swap-tokens.ts` — DEX swap
- `deploy-contract.ts` — Smart contract deployment
- `mint-carbon.ts` — Carbon credit minting

---

## CLI Tool

```bash
npm install -g @verdis/cli
```

### Commands

```bash
verdis chain info                         # Chain state
verdis chain block [number]               # Block header
verdis account create                     # New account
verdis account balance <address>          # Balance check
verdis account transfer <to> <amount>     # Transfer VRDX
verdis staking validators                 # List validators
verdis staking delegate <validator> <amount>  # Delegate
verdis dex pools                          # List pools
verdis dex swap <in> <out> <amt> <minOut> # Swap tokens
verdis eco projects                       # Reforestation projects
verdis eco green-score <validator>        # Green score
verdis contract call <addr> <method>      # Read contract
```

Global options: `-e, --endpoint <url>`, `--json`

---

## Cross-Chain Bridge

### Architecture

- **Ethereum → Verdis:** Lock tokens on Ethereum → Relayer detects Lock event → Mint on Verdis
- **Verdis → Ethereum:** Burn tokens on Verdis → Relayer detects burn → Unlock on Ethereum

### Security

- M-of-N relayer consensus (multi-relayer signatures required)
- EIP-712 typed data signatures
- Replay protection (burn tx hash uniqueness)
- Pausable emergency stops
- Fee mechanism (default 0.3%)

### Components

1. **VerdisBridge.sol** — Ethereum Solidity contract (`contracts/`)
2. **Relayer Service** — TypeScript service (`relayer/`)
3. **Bridge Pallet** — Substrate pallet (requires runtime integration)

See `verdis-bridge/README.md` for full documentation.

---

## RPC Methods

Verdis exposes 121 JSON-RPC methods. Key methods:

### Chain
- `chain_getBlock` — Get a block by hash
- `chain_getBlockHash` — Get block hash by number
- `chain_getFinalizedHead` — Get finalized head
- `chain_subscribeNewHeads` — Subscribe to new blocks (WebSocket)

### State
- `state_getStorage` — Query storage
- `state_getRuntimeVersion` — Runtime version
- `state_subscribeStorage` — Subscribe to storage changes

### System
- `system_health` — Node health
- `system_peers` — Connected peers
- `system_properties` — Chain properties (token, SS58)
- `system_name` — Node name

### Custom Verdis Methods
- `dpos_activeValidators` — List active DPoS validators
- `dpos_allValidators` — List all registered validators
- `dpos_validatorStake` — Get validator stake
- `dpos_currentEpoch` — Current epoch info
- `amm_dex_getAllPools` — List all DEX pools
- `amm_dex_getPrice` — Get swap price
- `amm_dex_getPool` — Get pool details
- `contracts_call` — Simulate contract call
- `contracts_getStorage` — Query contract storage

---

## Pallets & Runtime

13 pallets in the Verdis runtime:

| Pallet | Description |
|---|---|
| `Balances` | Native VRDX token balances and transfers |
| `Dpos` | DPoS consensus (validator selection, delegation, slashing) |
| `AmmDex` | AMM-based decentralized exchange |
| `Eco` | Carbon credits, reforestation, green scoring |
| `Vesting` | Token vesting schedules (30-60 day) |
| `Tokenomics` | Token supply management (100B total) |
| `FungibleTokens` | Custom token creation and management |
| `Contracts` | WASM smart contracts |
| `Nfts` | Non-fungible tokens |
| `Council` | Governance council (8 members) |
| `Democracy` | On-chain governance |
| `Treasury` | Treasury management |
| `Multisig` | Multi-signature accounts |
| `Proxy` | Account proxies |
| `Sudo` | Admin operations (restricted by call filter) |

---

## Smart Contracts

Verdis supports WASM-based smart contracts via `pallet-contracts`.

### RPC Methods
- `contracts_call` — Simulate read-only contract calls
- `contracts_getStorage` — Query contract storage
- `contracts_instantiate` — Deploy new contracts

### Using the SDK

```typescript
import { ContractsApi } from '@verdis/sdk';

const contracts = new ContractsApi(client.api);

// Read-only call
const result = await contracts.call('0x1234...', 'balance_of', ['0x5678...']);

// State-modifying call
const txResult = await contracts.execute(
  keypair,
  '0x1234...',
  'transfer',
  ['0x5678...', '1000000'],
  '0'
);
```

---

## DEX (AMM)

The Verdis DEX is a native AMM (Automated Market Maker) built directly into the runtime.

### Active Pools

| Pool | Pair | Fee |
|---|---|---|
| 1 | VRDX/ECO | 0.3% |
| 2 | VRDX/CARBON | 0.3% |
| 3 | VRDX/TREE | 0.3% |
| 4 | VRDX/GREEN | 0.3% |
| 5 | ECO/CARBON | 0.3% |
| 6 | VRDX/REDD | 0.3% |

### Using the SDK

```typescript
import { DexApi } from '@verdis/sdk';

const dex = new DexApi(client.api);

// List pools
const pools = await dex.getAllPools();

// Get price
const price = await dex.getPrice('VRDX', 'ECO');

// Swap
const result = await dex.swap(keypair, 'VRDX', 'ECO', '1000000000000000000', '900000000000000000');

// Add liquidity
const lpResult = await dex.addLiquidity(keypair, 'VRDX', 'ECO', '1000000000000000000', '500000000000000000');
```

---

## Eco Protocol

Verdis's eco protocol tracks environmental impact on-chain:

### Features
- **Carbon Credits** — Minted from verified reforestation projects
- **Reforestation Logging** — On-chain registry of tree-planting projects
- **Green Validator Scoring** — Validators scored by renewable energy usage
- **Carbon Retirement** — Permanently retire carbon credits

### Using the SDK

```typescript
import { EcoApi } from '@verdis/sdk';

const eco = new EcoApi(client.api);

// Check carbon credit balance
const credits = await eco.getCarbonCredits(keypair.address);

// List reforestation projects
const projects = await eco.getReforestationProjects();

// Check validator green score
const score = await eco.getGreenScore('5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY');

// Mint carbon credits (requires authority)
const result = await eco.mintCarbonCredits(authorityKeypair, '1000000000000000000', 'IPFS_PROOF_HASH');
```

---

## Staking (DPoS)

Verdis uses Delegated Proof of Stake for validator selection.

### Key Information
- 14 active validators (top stake)
- Session period: 600 blocks (~1 hour)
- BABE epoch: 100,000 slots (~6.9 days)
- Slashing: 5% on equivocation (VerdisOffenceHandler)

### Using the SDK

```typescript
import { StakingApi } from '@verdis/sdk';

const staking = new StakingApi(client.api, client.keys);

// List active validators
const validators = await staking.getActiveValidators();

// Get epoch info
const epoch = await staking.getCurrentEpoch();

// Delegate to a validator
const result = await staking.delegate(keypair, '5GrwvaEF...', '1000000000000000000');

// Remove delegation
const undelegateResult = await staking.undelegate(keypair, '5GrwvaEF...');
```

---

## Tokenomics

| Category | Allocation | Amount | Vesting |
|---|---|---|---|
| Community | 35% | 35B VRDX | Eco protocol |
| Treasury | 20% | 20B VRDX | Governance |
| Team | 15% | 15B VRDX | Vesting |
| Investors | 10% | 10B VRDX | 30-60 day vesting |
| Staking | 10% | 10B VRDX | Reward pool |
| Liquidity | 5% | 5B VRDX | DEX pools |
| Advisors | 3% | 3B VRDX | Vesting |
| Airdrop | 2% | 2B VRDX | Community |
| **Total** | **100%** | **100B VRDX** | |

---

## Security

### RPC Security
- 15 dangerous RPC methods blocked
- Per-IP connection limiting (max 10)
- Request size limit (1MB)
- Rate limiting (30 req/s)

### Network Security
- UFW firewall (ports 22, 80, 443, 30333 only)
- HSTS, X-Frame-Options, X-Content-Type-Options
- HTTP/2 with CORS restricted to verdischain.com
- Rate limiting per subdomain

### Blockchain Security
- VerdisBaseCallFilter blocks Sudo from public transactions
- VerdisOffenceHandler (5% slash on equivocation)
- 14 unique validator session keys
- GRANDPA finality

---

## Examples

See the `integration-examples/` directory for complete code examples:

1. `query-chain.ts` — Basic chain state queries
2. `create-wallet.ts` — Account creation and management
3. `transfer-vrdx.ts` — Token transfers
4. `delegate-stake.ts` — DPoS staking
5. `swap-tokens.ts` — DEX swap operations
6. `deploy-contract.ts` — Smart contract deployment
7. `mint-carbon.ts` — Carbon credit minting

### Running Examples

```bash
cd verdis-sdk/examples
npm install
npx tsx query-chain.ts
```

---

## License

MIT
