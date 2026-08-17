#!/bin/bash
# Analyze crypto tokens, check DeFi protocols, track wallets
# Usage: ./crypto-blockchain.sh "analyze BTC ETH"

QUERY="$1"
echo "📊 Crypto Analysis: $QUERY"

# Get top coins from CoinGecko
python3 -c "
import urllib.request
import json

# Get top coins
url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1'
req = urllib.request.Request(url, headers={'User-Agent': 'MrJames/6.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    print('Top 10 by Market Cap:')
    print(f'{'Name':15} {'Symbol':8} {'Price':>12} {'24h %':>8} {'MCap':>15}')
    print('-' * 65)
    for coin in data[:10]:
        name = coin['name'][:14]
        sym = coin['symbol'].upper()[:7]
        price = f\"\${coin['current_price']:,.2f}\"
        change = f\"{coin['price_change_percentage_24h']:+.1f}%\"
        mcap = f\"\${coin['market_cap']/1e9:.1f}B\"
        print(f'{name:15} {sym:8} {price:>12} {change:>8} {mcap:>15}')
except Exception as e:
    print(f'Error fetching data: {e}')
"

echo ""
echo "DeFi TVL (Top Protocols):"
python3 -c "
import urllib.request
import json
url = 'https://api.llama.fi/v2/protocols'
req = urllib.request.Request(url, headers={'User-Agent': 'MrJames/6.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    # Sort by TVL
    sorted_data = sorted(data, key=lambda x: x.get('tvl', 0), reverse=True)
    print(f'{'Protocol':20} {'Chain':12} {'TVL':>15}')
    print('-' * 50)
    for p in sorted_data[:5]:
        name = p['name'][:19]
        chain = (p.get('chain') or 'multi')[:11]
        tvl = f\"\${p.get('tvl', 0)/1e9:.2f}B\"
        print(f'{name:20} {chain:12} {tvl:>15}')
except Exception as e:
    print(f'Error: {e}')
"
