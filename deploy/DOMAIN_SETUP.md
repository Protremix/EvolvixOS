# EvolvixOS — Domain & DNS Configuration Guide

## evolvixos.com Setup

### 1. Domain Registration
If you don't own evolvixos.com yet, register it at:
- Namecheap: https://www.namecheap.com
- Cloudflare: https://www.cloudflare.com
- Google Domains: https://domains.google

### 2. DNS Configuration

Point these records to your server IP (e.g., `159.203.100.50`):

```
Type    Name   Value              TTL
A       @      159.203.100.50     300
A       www    159.203.100.50     300
CNAME   api    evolvixos.com      300
```

### 3. Cloudflare (Recommended)

1. Add evolvixos.com to Cloudflare
2. Change nameservers at your registrar
3. Add DNS records:
   - A record: @ → server IP (Proxied)
   - A record: www → server IP (Proxied)
   - CNAME: api → evolvixos.com (Proxied)
4. SSL/TLS mode: Full (strict)
5. Enable: Always Use HTTPS, HSTS, Auto Minify

### 4. Server Requirements

Minimum:
- 4 CPU cores
- 16 GB RAM
- 50 GB disk
- Ubuntu 22.04 LTS

Recommended (for GPU AI):
- 8 CPU cores
- 32 GB RAM
- 100 GB SSD
- NVIDIA GPU (RTX 3060+ or A10G)
- Ubuntu 22.04 LTS

### 5. Firewall (UFW)

```bash
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw enable
```

### 6. SSL Certificate (Let's Encrypt)

```bash
# Automatic (handled by deploy.sh):
certbot --nginx -d evolvixos.com -d www.evolvixos.com \
    --non-interactive --agree-tos -m admin@evolvixos.com --redirect

# Auto-renewal:
crontab -e
0 3 * * * certbot renew --quiet
```

### 7. Post-Deployment Checklist

- [ ] DNS records point to server
- [ ] Docker containers running
- [ ] Nginx serving landing page at http://evolvixos.com
- [ ] API accessible at https://evolvixos.com/api/v1/status
- [ ] Ollama models pulled (deepseek-r1, qwen2.5-coder, llama3.2)
- [ ] Auto-learner running (check: docker logs evolvix-learner)
- [ ] SSL certificate active
- [ ] Firewall configured
- [ ] Health check passing: curl https://evolvixos.com/health

### 8. Management Commands

```bash
# View logs
docker logs evolvix-core -f       # API server
docker logs evolvix-learner -f   # Auto-learner
docker logs evolvix-ollama -f     # LLM engine

# Restart services
docker compose -f deploy/docker-compose.yml restart

# Update EvolvixOS
git pull && docker compose -f deploy/docker-compose.yml up -d --build

# Check status
curl https://evolvixos.com/api/v1/status | python3 -m json.tool
```
