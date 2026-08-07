# Verdis Blockchain — First Fully Green Blockchain Ecosystem

Verdis (VCO) is the world's first fully green, carbon-negative blockchain with native DPoS consensus, on-chain carbon credits, reforestation logging, and green validator scoring.

## Features

- **DPoS Consensus** — 27 registered validators, auto block production every 5s
- **Native AMM DEX** — 6 liquidity pools (CARBON/VCO, ECO/VCO, CARBON/ECO, GREEN/VCO, SOLR/VCO, TST/VCO)
- **Stack-based VM** — 6 deployed smart contracts with 22+ opcodes
- **Eco System** — Carbon credit minting, reforestation tracking, green validator scoring
- **JSON-RPC** — Ethereum-compatible (Chain ID 909, Keccak-256 addresses)
- **Security** — secp256k1 signatures, SHA-256 hashing, rate limiting, input validation
- **API Key Management** — 8 endpoints, 4 permission scopes (read, trade, write, admin)
- **Native Android Wallet** — Standalone wallet with SHA-256 signing (no MetaMask dependency)

## Architecture

```
app/src/
├── api/          # REST API server + JSON-RPC
├── core/         # Blockchain core (block, consensus, DEX, eco, VM, security)
├── crypto/       # secp256k1 + SHA-256 cryptography
├── wallet/       # Wallet manager
└── web/          # 13 HTML pages (dashboard, explorer, DEX, etc.)
```

## Quick Start

```bash
cd app
npm install
npm run build
npm start
# Server runs on port 3200
```

## Live Deployment

- **Website**: https://verdischain.com
- **RPC**: https://rpc.verdischain.com
- **API Docs**: https://verdischain.com/api-docs
- **Explorer**: https://verdischain.com/explorer
- **APK**: https://verdischain.com/download/verdis-wallet.apk

## Tech Stack

- TypeScript / Node.js
- @noble/secp256k1 + @noble/hashes
- Express.js REST API
- Android (Kotlin + OkHttp + Gson)
- Nginx + systemd deployment

## License

MIT
