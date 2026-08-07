# Verdis SDK — API Reference

## Core Module

### VerdisClient

```typescript
class VerdisClient {
  /**
   * Create a new Verdis client.
   * @param options.endpoint - WebSocket endpoint URL
   * @param options.autoConnect - Connect immediately (default: true)
   */
  constructor(options: { endpoint: string; autoConnect?: boolean })

  /** Connect to the Verdis network */
  connect(): Promise<void>

  /** Disconnect from the network */
  disconnect(): Promise<void>

  /** Get current chain state */
  getChainState(): Promise<ChainState>

  /** Get balance for an address */
  getBalance(address: string): Promise<BalanceInfo>

  /** @polkadot/api instance for direct access */
  api: ApiPromise

  /** Key management utility */
  keys: VerdisKeyring

  /** Chain query helpers */
  chain: ChainQueries

  /** System query helpers */
  system: SystemQueries

  /** Transaction builder */
  tx: TransactionBuilder
}
```

### Types

```typescript
interface ChainState {
  chain: string;
  nodeName: string;
  nodeVersion: string;
  latestBlockNumber: number;
  latestBlockHash: string;
  genesisHash: string;
  ss58Prefix: number;
  tokenSymbol: string;
  tokenDecimals: number;
  totalIssuance: string;
  activeValidators: number;
}

interface BalanceInfo {
  free: string;
  reserved: string;
  miscFrozen: string;
  feeFrozen: string;
}

interface TxResult {
  txHash: string;
  blockHash: string;
  blockNumber: number;
  success: boolean;
  events: any[];
}
```

---

## Keyring Module

### Functions

```typescript
/** Generate a BIP39 mnemonic */
function generateMnemonic(length?: 12 | 15 | 18 | 21 | 24): string

/** Create a keypair from mnemonic */
function createKeypair(
  mnemonicOrUri: string,
  meta?: Record<string, any>,
  type?: 'sr25519' | 'ed25519' | 'ecdsa'
): KeyringPair

/** Import an account from mnemonic */
function importAccount(
  mnemonic: string,
  meta?: Record<string, any>
): KeyringPair

/** Sign and submit a transaction */
function signAndSubmit(
  api: ApiPromise,
  tx: SubmittableExtrinsic,
  keypair: KeyringPair
): Promise<TxResult>
```

### VerdisKeyring Class

```typescript
class VerdisKeyring {
  constructor(options?: { ss58Format?: number; type?: KeypairType })

  /** Create keypair from mnemonic */
  createKeypair(mnemonic: string, meta?: object): KeyringPair

  /** Import account from mnemonic */
  importAccount(mnemonic: string, meta?: object): KeyringPair

  /** Sign and submit transaction */
  signAndSubmit(
    api: ApiPromise,
    tx: SubmittableExtrinsic,
    keypair: KeyringPair
  ): Promise<TxResult>

  /** SS58 format */
  static readonly VERDIS_SS58_PREFIX = 909
}
```

---

## Staking Module

### StakingApi

```typescript
class StakingApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)

  /** Get list of active validator addresses */
  getActiveValidators(): Promise<string[]>

  /** Get current epoch information */
  getCurrentEpoch(): Promise<EpochInfo>

  /** Delegate stake to a validator */
  delegate(
    account: KeyringPair,
    validator: string,
    amount: string
  ): Promise<TxResult>

  /** Remove delegation from a validator */
  undelegate(
    account: KeyringPair,
    validator: string
  ): Promise<TxResult>
}

interface EpochInfo {
  sessionIndex: number;
  era: number;
  validators: string[];
}
```

---

## DEX Module

### DexApi

```typescript
class DexApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)

  /** Get all liquidity pools */
  getAllPools(): Promise<PoolInfo[]>

  /** Get a specific pool by ID */
  getPool(poolId: number): Promise<PoolInfo>

  /** Get swap price between two assets */
  getPrice(assetIn: string, assetOut: string): Promise<PriceInfo>

  /** Execute a swap */
  swap(
    account: KeyringPair,
    assetIn: string,
    assetOut: string,
    amountIn: string,
    minAmountOut: string
  ): Promise<TxResult>

  /** Add liquidity to a pool */
  addLiquidity(
    account: KeyringPair,
    assetA: string,
    assetB: string,
    amountA: string,
    amountB: string
  ): Promise<TxResult>
}

interface PoolInfo {
  poolId: number;
  tokenA: string;
  tokenB: string;
  reserveA: string;
  reserveB: string;
  totalLiquidity: string;
  feeBps: number;
}

interface PriceInfo {
  price: string;
  inputReserve: string;
  outputReserve: string;
  feeBps: number;
}
```

---

## Eco Module

### EcoApi

```typescript
class EcoApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)

  /** Get carbon credit balance for an address */
  getCarbonCredits(address: string): Promise<string>

  /** List all reforestation projects */
  getReforestationProjects(): Promise<ProjectInfo[]>

  /** Get green score for a validator */
  getGreenScore(validator: string): Promise<number | null>

  /** Mint carbon credits (requires authority) */
  mintCarbonCredits(
    account: KeyringPair,
    amount: string,
    proof: string
  ): Promise<TxResult>
}

interface ProjectInfo {
  id: string;
  name: string;
  developer: string;
  carbonCreditsIssued: string;
  carbonCreditsRetired: string;
  category: string;
  certified: boolean;
}
```

---

## Contracts Module

### ContractsApi

```typescript
class ContractsApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)

  /** Read-only contract call (no state change) */
  call(
    address: string,
    method: string,
    args?: any[]
  ): Promise<ContractResult>

  /** Execute a state-modifying contract call */
  execute(
    account: KeyringPair,
    address: string,
    method: string,
    args?: any[],
    value?: string
  ): Promise<TxResult>

  /** Get the code hash of a contract */
  getCodeHash(address: string): Promise<string | null>
}

interface ContractResult {
  gasConsumed: string;
  output: string | null;
  isError: boolean;
  errorMessage: string | null;
}
```

---

## Tokens Module

### TokenApi

```typescript
class TokenApi {
  constructor(api: ApiPromise, keys?: VerdisKeyring)

  /** Create a new fungible token */
  create(
    account: KeyringPair,
    name: string,
    symbol: string,
    decimals: number,
    totalSupply: string
  ): Promise<TxResult>

  /** Get token info */
  getInfo(tokenId: string): Promise<TokenInfo>

  /** Get token balance */
  getBalance(tokenId: string, address: string): Promise<string>

  /** Transfer tokens */
  transfer(
    account: KeyringPair,
    tokenId: string,
    to: string,
    amount: string
  ): Promise<TxResult>
}
```
