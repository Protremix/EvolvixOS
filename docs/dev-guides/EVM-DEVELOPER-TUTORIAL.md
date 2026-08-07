# Verdis EVM Developer Tutorial

## Quick Start

### 1. Install Tools

```bash
# Install Node.js 18+ and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Foundry (recommended for Verdis)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Or use Hardhat
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
```

### 2. Configure Network

**MetaMask Setup:**
| Field | Value |
|---|---|
| Network Name | Verdis |
| RPC URL | `https://verdischain.com/rpc` |
| Chain ID | `909` |
| Symbol | `VRDX` |
| Block Explorer | `https://verdischain.com/explorer` |

**Hardhat Configuration:**
```javascript
// hardhat.config.js
module.exports = {
  solidity: "0.8.20",
  networks: {
    verdis: {
      url: "https://verdischain.com/rpc",
      chainId: 909,
      accounts: [process.env.PRIVATE_KEY],
      gasPrice: 1000000000, // 1 Gwei
    },
    verdis_testnet: {
      url: "https://testnet.verdischain.com/rpc",
      chainId: 909,
      accounts: [process.env.PRIVATE_KEY],
    }
  }
};
```

**Foundry Configuration:**
```bash
# foundry.toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
chain_id = 909
```

### 3. Deploy Your First Contract

**Create `src/MyToken.sol`:**
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MyToken is ERC20 {
    constructor(uint256 initialSupply) ERC20("My Token", "MYT") {
        _mint(msg.sender, initialSupply);
    }
}
```

**Deploy with Foundry:**
```bash
forge create src/MyToken.sol:MyToken \
  --constructor-args 1000000000000000000000000 \
  --rpc-url https://verdischain.com/rpc \
  --private-key $PRIVATE_KEY \
  --chain-id 909
```

**Deploy with Hardhat:**
```javascript
// scripts/deploy.js
const hre = require("hardhat");

async function main() {
  const MyToken = await hre.ethers.getContractFactory("MyToken");
  const token = await MyToken.deploy(
    hre.ethers.parseUnits("1000000", 18)
  );
  await token.waitForDeployment();
  console.log("Deployed to:", await token.getAddress());
}

main().catch(console.error);
```

```bash
npx hardhat run scripts/deploy.js --network verdis
```

### 4. Interact with Contracts

**Using ethers.js:**
```javascript
const { ethers } = require("ethers");

const provider = new ethers.JsonRpcProvider("https://verdischain.com/rpc");
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);

const tokenAbi = [
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function totalSupply() view returns (uint256)",
  "function balanceOf(address) view returns (uint256)",
  "function transfer(address to, uint256 amount) returns (bool)"
];

const token = new ethers.Contract(
  "0x...", // contract address
  tokenAbi,
  wallet
);

// Read token info
const name = await token.name();
const supply = await token.totalSupply();
console.log(`${name}: ${ethers.formatUnits(supply, 18)} tokens`);

// Transfer tokens
const tx = await token.transfer(
  "0x...", // recipient
  ethers.parseUnits("100", 18)
);
await tx.wait();
console.log("Transfer complete!");
```

### 5. Carbon Credit Tutorial

Deploy and interact with carbon credits:

```javascript
const carbonAbi = [
  "function issueCredit(address to, uint256 amount, string project, string location) returns (uint256)",
  "function retireCredit(uint256 creditId, uint256 amount)",
  "function getCreditInfo(uint256 creditId) returns (uint256, uint256, string, string, uint256, bool)",
  "function getNetCarbon() view returns (uint256)"
];

// Issue a carbon credit
const tx = await carbon.issueCredit(
  recipient,
  100, // 100 tons CO2
  "Amazon Reforestation",
  "Brazil"
);

// Check net carbon
const netCarbon = await carbon.getNetCarbon();
console.log("Net carbon offset:", netCarbon, "tons");
```

### 6. Gas Estimation

| Operation | Gas | VRDX (at 1 Gwei) |
|---|---|---|
| Simple transfer | 21,000 | 0.000021 |
| ERC-20 transfer | 51,000 | 0.000051 |
| Contract deploy | 1,000,000+ | 0.001+ |
| Carbon credit issue | 150,000 | 0.00015 |
| Validator score update | 80,000 | 0.00008 |

### 7. Verifying Contracts

Verify on Verdiscan:
```bash
forge verify-contract <address> src/MyToken.sol:MyToken \
  --verifier verdiscan \
  --verifier-url https://verdischain.com/api/verify
```

### 8. Common Patterns

**Reentrancy Protection:**
```solidity
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SafeContract is ReentrancyGuard {
    function withdraw() external nonReentrant {
        // Safe from reentrancy
    }
}
```

**Access Control:**
```solidity
import "@openzeppelin/contracts/access/AccessControl.sol";

contract RoleBased is AccessControl {
    bytes32 public constant VERIFIER = keccak256("VERIFIER");
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
    }
}
```

---

*Questions? Join the Verdis developer community on GitHub Discussions.*
*Last updated: August 5, 2026*

## 9. Troubleshooting

### "Nonce too low" error
Your local nonce is out of sync. Reset MetaMask:
```
Settings → Advanced → Reset account
```
Or use Hardhat with `nonce: await provider.getTransactionCount(address)`.

### "Insufficient funds for gas"
You need VRDX for gas. Get testnet tokens from the faucet:
```bash
curl -X POST https://testnet.verdischain.com/faucet \
  -H "Content-Type: application/json" \
  -d '{"address": "your_address"}'
```

### "Contract code size exceeds limit"
EIP-170 limits contracts to 24,576 bytes. Enable optimizer:
```javascript
// hardhat.config.js
solidity: {
  compiler: { version: "0.8.20" },
  settings: { optimizer: { enabled: true, runs: 200 } }
}
```

### "Execution reverted"
Common causes:
1. Require statement failed — check function arguments
2. Access control — verify msg.sender has required role
3. Pausable contract paused — call unpause()
4. Insufficient balance — check token balance
5. Allowance too low — call approve() first

### "Chain ID mismatch"
Ensure your config uses Chain ID 909:
```javascript
// Hardhat
networks: { verdis: { chainId: 909 } }
// Foundry
forge create ... --chain-id 909
```

### "Gas estimation failed"
Try setting gas limit manually:
```bash
forge create ... --gas-limit 3000000
```

### OpenZeppelin imports not found
Install OpenZeppelin:
```bash
# Foundry
forge install OpenZeppelin/openzeppelin-contracts

# Hardhat
npm install @openzeppelin/contracts
```

### RPC connection refused
Check the node is running:
```bash
curl -X POST https://verdischain.com/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"system_health","id":1}'
```
