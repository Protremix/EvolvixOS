# Verdis Integration Examples

Complete code examples for integrating with the Verdis Blockchain.

## Prerequisites

```bash
npm install @verdis/sdk
```

All examples assume a connected VerdisClient:

```typescript
import { VerdisClient } from '@verdis/sdk';

const client = new VerdisClient({
  endpoint: 'wss://verdischain.com/ws',
});

await client.connect();
```

---

## 1. Query Chain State

```typescript
// file: query-chain.ts
import { VerdisClient } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({
    endpoint: 'wss://verdischain.com/ws',
  });
  await client.connect();

  const state = await client.getChainState();
  console.log('Chain:', state.chain);
  console.log('Token:', state.tokenSymbol, `(${state.tokenDecimals} decimals)`);
  console.log('SS58:', state.ss58Prefix);
  console.log('Block:', state.latestBlockNumber);
  console.log('Validators:', state.activeValidators);
  console.log('Total Issuance:', state.totalIssuance, 'Planck');

  const health = await client.system.getHealth();
  console.log('Peers:', health.peers);
  console.log('Syncing:', health.isSyncing);

  await client.disconnect();
}

main();
```

---

## 2. Create Wallet & Check Balance

```typescript
// file: create-wallet.ts
import { generateMnemonic, createKeypair, VerdisClient } from '@verdis/sdk';

async function main() {
  // Generate new account
  const mnemonic = generateMnemonic();
  const keypair = createKeypair(mnemonic, { name: 'My Wallet' });

  console.log('Address:', keypair.address);
  console.log('Mnemonic:', mnemonic);
  console.log('⚠️  Save your mnemonic securely!');

  // Connect and check balance
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const balance = await client.getBalance(keypair.address);
  console.log('Free:', balance.free, 'Planck');
  console.log('Reserved:', balance.reserved, 'Planck');

  await client.disconnect();
}

main();
```

---

## 3. Transfer VRDX

```typescript
// file: transfer-vrdx.ts
import { VerdisClient, createKeypair } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const mnemonic = process.env.MNEMONIC!;
  const sender = createKeypair(mnemonic, { name: 'Sender' });

  const recipient = '5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty';
  const amount = '1000000000000000000'; // 1 VRDX (18 decimals)

  const tx = client.tx.transfer(recipient, amount);
  const result = await client.keys.signAndSubmit(client.api, tx, sender);

  console.log('Transaction:', result.txHash);
  console.log('Block:', result.blockHash);
  console.log('Success:', result.success);

  await client.disconnect();
}

main();
```

---

## 4. Delegate Stake (DPoS)

```typescript
// file: delegate-stake.ts
import { VerdisClient, createKeypair, StakingApi } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const mnemonic = process.env.MNEMONIC!;
  const account = createKeypair(mnemonic, { name: 'Delegator' });

  const staking = new StakingApi(client.api, client.keys);

  // List active validators
  const validators = await staking.getActiveValidators();
  console.log('Active validators:', validators);

  // Delegate to the first validator
  const validator = validators[0];
  const amount = '1000000000000000000'; // 1 VRDX

  const result = await staking.delegate(account, validator, amount);
  console.log('Delegated to:', validator);
  console.log('Tx:', result.txHash);

  await client.disconnect();
}

main();
```

---

## 5. Swap Tokens on DEX

```typescript
// file: swap-tokens.ts
import { VerdisClient, createKeypair, DexApi } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const mnemonic = process.env.MNEMONIC!;
  const account = createKeypair(mnemonic, { name: 'Swapper' });

  const dex = new DexApi(client.api, client.keys);

  // List all pools
  const pools = await dex.getAllPools();
  console.log('Pools:', pools.length);
  pools.forEach(p => {
    console.log(`  Pool #${p.poolId}: ${p.tokenA}/${p.tokenB} — Reserve: ${p.reserveA}/${p.reserveB}`);
  });

  // Get price
  const price = await dex.getPrice('VRDX', 'ECO');
  console.log('Price:', price.price);
  console.log('Fee:', price.feeBps, 'bps');

  // Execute swap: 1 VRDX → ECO (min 0.9 ECO)
  const result = await dex.swap(
    account,
    'VRDX',
    'ECO',
    '1000000000000000000',
    '900000000000000000'
  );
  console.log('Swap tx:', result.txHash);

  await client.disconnect();
}

main();
```

---

## 6. Deploy & Call Smart Contract

```typescript
// file: deploy-contract.ts
import { VerdisClient, createKeypair, ContractsApi } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const mnemonic = process.env.MNEMONIC!;
  const account = createKeypair(mnemonic, { name: 'Deployer' });

  const contracts = new ContractsApi(client.api, client.keys);

  // Read-only call to an existing contract
  const contractAddress = '0x1234567890abcdef...';
  const result = await contracts.call(contractAddress, 'balance_of', [
    account.address,
  ]);
  console.log('Balance:', result.output);
  console.log('Gas:', result.gasConsumed);

  // State-modifying call
  const txResult = await contracts.execute(
    account,
    contractAddress,
    'transfer',
    ['0x5678...', '1000000'],
    '0'
  );
  console.log('Tx:', txResult.txHash);

  // Get code hash
  const codeHash = await contracts.getCodeHash(contractAddress);
  console.log('Code hash:', codeHash);

  await client.disconnect();
}

main();
```

---

## 7. Mint Carbon Credits

```typescript
// file: mint-carbon.ts
import { VerdisClient, createKeypair, EcoApi } from '@verdis/sdk';

async function main() {
  const client = new VerdisClient({ endpoint: 'wss://verdischain.com/ws' });
  await client.connect();

  const mnemonic = process.env.AUTHORITY_MNEMONIC!;
  const authority = createKeypair(mnemonic, { name: 'Eco Authority' });

  const eco = new EcoApi(client.api, client.keys);

  // List reforestation projects
  const projects = await eco.getReforestationProjects();
  console.log('Projects:', projects.length);
  projects.forEach(p => {
    console.log(`  ${p.name} — Issued: ${p.carbonCreditsIssued}, Retired: ${p.carbonCreditsRetired}`);
  });

  // Check carbon credit balance
  const credits = await eco.getCarbonCredits(authority.address);
  console.log('Carbon credits:', credits, 'Planck');

  // Check validator green score
  const validators = await client.api.query.dpos.activeValidators();
  for (const v of validators) {
    const score = await eco.getGreenScore(v.toString());
    console.log(`Validator ${v}: Green Score = ${score ?? 'N/A'}`);
  }

  // Mint carbon credits (requires authority)
  const amount = '1000000000000000000'; // 1 CARBON
  const proof = 'IPFS_HASH_OF_VERIFICATION_DATA';
  const result = await eco.mintCarbonCredits(authority, amount, proof);
  console.log('Mint tx:', result.txHash);

  await client.disconnect();
}

main();
```

---

## Environment Setup

Create a `.env` file:

```bash
MNEMONIC="your twelve word mnemonic phrase here"
AUTHORITY_MNEMONIC="your authority mnemonic for eco operations"
```

Load it with `dotenv`:

```typescript
import 'dotenv/config';
```

---

## Running Examples

```bash
# Clone the SDK
git clone https://github.com/Protremix/Verdischain-

# Install dependencies
cd verdis-sdk && npm install

# Run individual examples
npx tsx examples/query-chain.ts
npx tsx examples/create-wallet.ts
npx tsx examples/transfer-vrdx.ts
npx tsx examples/delegate-stake.ts
npx tsx examples/swap-tokens.ts
npx tsx examples/deploy-contract.ts
npx tsx examples/mint-carbon.ts
```
