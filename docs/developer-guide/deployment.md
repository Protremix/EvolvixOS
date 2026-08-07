# Verdis Blockchain — Deployment Guide

## Server Information

| Property | Value |
|---|---|
| Server IP | 91.98.160.145 |
| OS | Ubuntu 22.04 LTS |
| Domain | verdischain.com |
| SSL | Let's Encrypt (expires Nov 2 2026) |

## Services

### Node Services (systemd)

| Service | Port | Description |
|---|---|---|
| verdis-boot-1 | 30333 | Boot node 1 |
| verdis-boot-2 | 30334 | Boot node 2 |
| verdis-rpc-1 | 9944 | RPC node 1 (localhost) |
| verdis-rpc-2 | 9949 | RPC node 2 (public via nginx) |
| verdis-validator-1..14 | 30335-30348 | 14 validator nodes |

### Web Services (nginx)

| Subdomain | Upstream | Description |
|---|---|---|
| verdischain.com | static | Landing page, blog, docs |
| explorer.verdischain.com | static | Verdiscan explorer |
| wallet.verdischain.com | static | Web wallet |
| docs.verdischain.com | static | Documentation |
| developers.verdischain.com | static | Developer portal |
| api.verdischain.com | node:3000 | REST API + faucet |
| rpc.verdischain.com | node:9949 | Substrate JSON-RPC |
| ws.verdischain.com | node:9949 | WebSocket |
| faucet.verdischain.com | static | Faucet UI |
| dex.verdischain.com | static | DEX interface |
| validators.verdischain.com | static | Validator dashboard |
| status.verdischain.com | :9090 | Grafana monitoring |

### Infrastructure

| Service | Port | Description |
|---|---|---|
| Prometheus | 9090 | Metrics collection (21 targets) |
| Grafana | 3001 | Monitoring dashboards |
| Nginx | 80/443 | Reverse proxy + SSL |

## Deployment Steps

### 1. SSH Access

```bash
ssh root@91.98.160.145
```

### 2. Node Management

```bash
# Check node status
systemctl status verdis-rpc-2

# Restart a node
systemctl restart verdis-rpc-2

# View logs
journalctl -u verdis-rpc-2 -f

# Check all nodes
for i in boot-1 boot-2 rpc-1 rpc-2 validator-{1..14}; do
  echo -n "verdis-$i: "; systemctl is-active verdis-$i
done
```

### 3. Chain Operations

```bash
# Check chain state
curl -s https://verdischain.com/rpc -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"system_health","params":[],"id":1}' | jq

# Check block height
curl -s https://verdischain.com/rpc -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"chain_getBlockHash","params":[],"id":1}' | jq

# Purge chain and restart (DESTRUCTIVE)
# Only do this for testing — never on mainnet!
systemctl stop verdis-*
verdis-node purge-chain --base-path /opt/verdis-data/rpc-2 --chain verdis-raw.json
systemctl start verdis-*
```

### 4. SSL Renewal

```bash
# SSL auto-renews via certbot. Verify:
certbot certificates

# Force renewal:
certbot renew --dry-run
```

### 5. Backup

```bash
# Daily backup runs at 2am via cron
# Manual backup:
/opt/verdis-backup.sh

# Backups stored at /opt/verdis-backups/ (30-day retention)
```

### 6. Monitoring

```bash
# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health' | sort | uniq -c

# Grafana
# Visit https://status.verdischain.com (credentials required)
```

## Firewall Rules

| Port | Service | Access |
|---|---|---|
| 22 | SSH | All |
| 80 | HTTP | All |
| 443 | HTTPS | All |
| 30333 | P2P | All |
| 9944 | RPC | localhost only |
| 9949 | RPC (public) | localhost (nginx proxy) |
| 9090 | Prometheus | localhost only |

## Emergency Procedures

### Bridge Pause
```bash
# Pause the bridge contract (requires PAUSER_ROLE on Ethereum)
# Use the CLI or web interface
```

### Node Recovery
```bash
# If a node crashes:
systemctl restart verdis-validator-5

# If chain is corrupted:
systemctl stop verdis-validator-5
rm -rf /opt/verdis-data/validator-5/db
systemctl start verdis-validator-5
```

### Full Network Restart
```bash
# Stop all nodes
for i in boot-1 boot-2 rpc-1 rpc-2 validator-{1..14}; do
  systemctl stop verdis-$i
done

# Wait 5 seconds
sleep 5

# Start in order
systemctl start verdis-boot-1
systemctl start verdis-boot-2
sleep 10
for i in rpc-1 rpc-2; do systemctl start verdis-$i; done
sleep 5
for i in validator-{1..14}; do systemctl start verdis-$i; done

# Verify
for i in boot-1 boot-2 rpc-1 rpc-2 validator-{1..14}; do
  echo -n "verdis-$i: "; systemctl is-active verdis-$i
done
```
