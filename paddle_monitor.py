#!/usr/bin/env python3
import os, json, time, urllib.request, urllib.error
from datetime import datetime

with open('/opt/evolvixos/.env') as f:
    for line in f:
        if line.startswith('PADDLE_API_KEY='):
            API_KEY = line.split('=', 1)[1].strip()
            break

API_BASE = 'https://api.paddle.com'

def check():
    r = {'time': datetime.now().strftime('%H:%M:%S'), 'domain': '?', 'tx': '?'}
    try:
        req = urllib.request.Request(API_BASE + '/checkout-domains?per_page=1',
            headers={'Authorization': 'Bearer ' + API_KEY})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        doms = data.get('data', [])
        if doms:
            r['domain'] = doms[0].get('status', '?')
    except Exception:
        pass
    try:
        body = json.dumps({'items': [{'price_id': 'pri_01m19494p7k6w88wkx56vctk3e', 'quantity': 1}]}).encode()
        req = urllib.request.Request(API_BASE + '/transactions', data=body, method='POST',
            headers={'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'})
        urllib.request.urlopen(req, timeout=10)
        r['tx'] = 'ENABLED'
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode())
        r['tx'] = body.get('error', {}).get('code', 'error')
    except Exception:
        pass
    return r

last = None
while True:
    r = check()
    cur = r['domain'] + '|' + r['tx']
    if cur != last:
        print('[{}] Domain: {} | TX: {}'.format(r['time'], r['domain'], r['tx']))
        if 'ENABLED' in str(r['tx']):
            print('=' * 50)
            print('  PADDLE ACCOUNT IS ACTIVE!')
            print('=' * 50)
        last = cur
    time.sleep(600)
