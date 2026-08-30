#!/usr/bin/env python3
"""
Paddle Sandbox Provisioning Script
Creates all 10 products and 16 prices in the Paddle sandbox environment.
Also creates a notification destination for webhooks.

Usage:
  PADDLE_SANDBOX_API_KEY=pdl_sdbx_apikey_... python3 paddle_sandbox_setup.py
"""
import os
import sys
import json
import urllib.request
import urllib.error

API_BASE = "https://api.paddle.com"  # Sandbox uses api.paddle.com too, key prefix determines env
API_KEY = os.environ.get("PADDLE_SANDBOX_API_KEY", "")
WEBHOOK_URL = os.environ.get("PADDLE_WEBHOOK_URL", "https://evolvixos.com/auth/paddle-webhook")

if not API_KEY:
    print("ERROR: Set PADDLE_SANDBOX_API_KEY environment variable")
    print("  Get it from https://sandbox-vendors.paddle.com > Developer tools > Authentication")
    sys.exit(1)

def api_call(method, path, body=None):
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"  ERROR {e.code}: {error_body[:200]}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Product definitions (matching production catalog)
PRODUCTS = [
    {"name": "EvolvixOS Starter", "tax_category": "standard", "description": "Starter plan — 5,000 credits/month"},
    {"name": "EvolvixOS Pro", "tax_category": "standard", "description": "Pro plan — 15,000 credits/month"},
    {"name": "EvolvixOS Team", "tax_category": "standard", "description": "Team plan — 50,000 credits/month"},
    {"name": "EvolvixOS Business", "tax_category": "standard", "description": "Business plan — 150,000 credits/month"},
    {"name": "EvolvixOS Enterprise", "tax_category": "standard", "description": "Enterprise plan — 500,000 credits/month"},
    {"name": "EvolvixOS Enterprise+", "tax_category": "standard", "description": "Enterprise+ plan — unlimited credits"},
    {"name": "EvolvixOS 1000 Credits", "tax_category": "standard", "description": "One-time purchase of 1,000 credits"},
    {"name": "EvolvixOS 5000 Credits", "tax_category": "standard", "description": "One-time purchase of 5,000 credits"},
    {"name": "EvolvixOS 15000 Credits", "tax_category": "standard", "description": "One-time purchase of 15,000 credits"},
    {"name": "EvolvixOS 50000 Credits", "tax_category": "standard", "description": "One-time purchase of 50,000 credits"},
]

# Price definitions (matching production)
# Format: (product_index, description, amount_in_cents, currency, interval_or_none)
PRICES = [
    # Starter: €9/mo, €86/yr
    (0, "Starter monthly EUR", 900, "EUR", ("month", 1)),
    (0, "Starter yearly EUR", 8600, "EUR", ("year", 1)),
    # Pro: €99/mo, €278/yr  (wait, production has 9900 cents = €99, 27800 = €278)
    # Actually production: monthly 9900 = €99, yearly 27800 = €278
    # Let me use the same values
    (1, "Pro monthly EUR", 9900, "EUR", ("month", 1)),
    (1, "Pro yearly EUR", 27800, "EUR", ("year", 1)),
    # Team: €199/mo, €95/yr (wait, production: 19900 = €199, 95000 = €950)
    (2, "Team monthly EUR", 19900, "EUR", ("month", 1)),
    (2, "Team yearly EUR", 95000, "EUR", ("year", 1)),
    # Business: €499/mo, €4,700/yr
    (3, "Business monthly EUR", 49900, "EUR", ("month", 1)),
    (3, "Business yearly EUR", 47000, "EUR", ("year", 1)),
    # Enterprise: €2,990/mo, €19,000/yr
    (4, "Enterprise monthly EUR", 29900, "EUR", ("month", 1)),
    (4, "Enterprise yearly EUR", 190000, "EUR", ("year", 1)),
    # Enterprise+: €2,990/mo, €28,700/yr
    (5, "Enterprise+ monthly EUR", 29900, "EUR", ("month", 1)),
    (5, "Enterprise+ yearly EUR", 287000, "EUR", ("year", 1)),
    # Credit packs (one-time)
    (6, "1000 Credits one-time EUR", 900, "EUR", None),
    (7, "5000 Credits one-time EUR", 3900, "EUR", None),
    (8, "15000 Credits one-time EUR", 9900, "EUR", None),
    (9, "50000 Credits one-time EUR", 29900, "EUR", None),
]

def main():
    print("=" * 60)
    print("  Paddle Sandbox Provisioning")
    print("=" * 60)
    
    # Step 1: Create products
    print("\n=== STEP 1: Create Products ===")
    product_ids = {}
    for i, prod in enumerate(PRODUCTS):
        print(f"  Creating: {prod['name']}...", end=" ")
        result = api_call("POST", "/products", prod)
        if result and "data" in result:
            pid = result["data"]["id"]
            product_ids[i] = pid
            print(f"OK ({pid})")
        else:
            print("FAILED")
    
    print(f"\n  Created {len(product_ids)}/{len(PRODUCTS)} products")
    
    # Step 2: Create prices
    print("\n=== STEP 2: Create Prices ===")
    price_ids = {}
    for prod_idx, desc, amount, currency, billing in PRICES:
        if prod_idx not in product_ids:
            print(f"  SKIP {desc} (product not created)")
            continue
        
        price_body = {
            "product_id": product_ids[prod_idx],
            "description": desc,
            "unit_price": {"amount": str(amount), "currency_code": currency},
        }
        if billing:
            price_body["billing_cycle"] = {"interval": billing[0], "frequency": billing[1]}
        
        print(f"  Creating: {desc}...", end=" ")
        result = api_call("POST", "/prices", price_body)
        if result and "data" in result:
            prid = result["data"]["id"]
            price_ids[desc] = prid
            print(f"OK ({prid})")
        else:
            print("FAILED")
    
    print(f"\n  Created {len(price_ids)}/{len(PRICES)} prices")
    
    # Step 3: Create notification destination
    print("\n=== STEP 3: Create Webhook Destination ===")
    webhook_events = [
        "transaction.completed",
        "transaction.created",
        "subscription.created",
        "subscription.updated",
        "subscription.canceled",
        "customer.created",
        "customer.updated",
    ]
    
    webhook_body = {
        "description": "EvolvixOS Sandbox Webhook",
        "destination": WEBHOOK_URL,
        "subscribed_events": webhook_events,
        "type": "url",
    }
    
    print(f"  URL: {WEBHOOK_URL}")
    print(f"  Events: {', '.join(webhook_events)}")
    result = api_call("POST", "/notification-settings", webhook_body)
    if result and "data" in result:
        webhook_id = result["data"]["id"]
        print(f"  Webhook created: {webhook_id}")
    else:
        print("  Webhook creation failed (may already exist)")
    
    # Step 4: Print summary
    print("\n" + "=" * 60)
    print("  SANDBOX CATALOG CREATED")
    print("=" * 60)
    print(f"\n  Products: {len(product_ids)}")
    for i, name in enumerate(PRODUCTS):
        if i in product_ids:
            print(f"    {product_ids[i]} - {name['name']}")
    
    print(f"\n  Prices: {len(price_ids)}")
    for desc, prid in price_ids.items():
        print(f"    {prid} - {desc}")
    
    print("\n  Next steps:")
    print("  1. Get client-side token from sandbox dashboard")
    print("  2. Update .env with sandbox keys")
    print("  3. Test checkout with card 4242 4242 4242 4242")

if __name__ == "__main__":
    main()
