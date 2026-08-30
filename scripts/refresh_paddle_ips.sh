#!/bin/bash
# Fetch current Paddle webhook IPs and update nginx allowlist
# Source of truth: https://api.paddle.com/ips
# Run via cron: 0 */6 * * * /opt/evolvixos/scripts/refresh_paddle_ips.sh

IPS=$(curl -s --max-time 10 https://api.paddle.com/ips | python3 -c '
import sys, json
r = json.load(sys.stdin)
cidrs = r.get("data", {}).get("ipv4_cidrs", [])
ips = [c.split("/")[0] for c in cidrs]
print("\n".join(ips))
')

if [ -z "$IPS" ]; then
    echo "Failed to fetch Paddle IPs" >&2
    exit 1
fi

cat > /etc/nginx/snippets/paddle-allowlist.conf << NGINXEOF
# Paddle webhook IP allowlist
# Source: https://api.paddle.com/ips (fetched dynamically)
# Last updated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
NGINXEOF

echo "$IPS" | while read ip; do
    echo "allow $ip;" >> /etc/nginx/snippets/paddle-allowlist.conf
done
echo 'deny all;' >> /etc/nginx/snippets/paddle-allowlist.conf

nginx -t 2>/dev/null && nginx -s reload 2>/dev/null
echo "Paddle IP allowlist refreshed: $(echo $IPS | wc -w) IPs"
