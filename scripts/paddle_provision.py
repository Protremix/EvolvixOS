#!/usr/bin/env python3
"""Provision EvolvixOS products and prices in Paddle Billing.

Reads plan definitions from the auth database and creates one Paddle product per
plan with monthly + yearly prices, plus one-time products for each credit pack.
Idempotent: existing products are matched by name and reused, and existing prices
are matched by billing cycle so re-running will not duplicate anything.

Defaults to SANDBOX. Point PADDLE_API_BASE at https://api.paddle.com to go live.

    export PADDLE_API_KEY=pdl_sdbx_apikey_...
    python3 paddle_provision.py --dry-run
    python3 paddle_provision.py

Writes the resulting price IDs to paddle_prices.json, which the checkout layer
loads to map plan+cycle -> Paddle price id.
"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request

API_KEY = os.environ.get("PADDLE_API_KEY", "")
API_BASE = os.environ.get("PADDLE_API_BASE", "https://api.paddle.com")
DB_PATH = os.environ.get("EVOLVIX_AUTH_DB", "/opt/evolvixos/auth/users.db")
OUT_FILE = os.environ.get("PADDLE_PRICES_FILE", "paddle_prices.json")
CURRENCY = os.environ.get("PADDLE_CURRENCY", "EUR")

# Credit packs: (credits, price in major units)
CREDIT_PACKS = [(1000, 9), (5000, 39), (15000, 99), (50000, 299)]


def api(method, path, payload=None):
    url = API_BASE.rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise SystemExit(f"Paddle API {method} {path} failed: {e.code}\n{body}")


def list_all(path, key="data"):
    """Paginate a Paddle list endpoint fully."""
    out, after = [], None
    while True:
        p = f"{path}?per_page=200" + (f"&after={after}" if after else "")
        resp = api("GET", p)
        batch = resp.get(key, [])
        out.extend(batch)
        meta = (resp.get("meta") or {}).get("pagination") or {}
        if not meta.get("has_more") or not batch:
            break
        after = batch[-1]["id"]
    return out


def load_plans():
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"auth DB not found at {DB_PATH}")
    cn = sqlite3.connect(DB_PATH)
    rows = cn.execute(
        "SELECT name, price_monthly, price_yearly, credits_monthly FROM plans "
        "WHERE is_active = 1 AND price_monthly > 0 ORDER BY sort_order").fetchall()
    cn.close()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be created without calling Paddle")
    args = ap.parse_args()

    if not args.dry_run and not API_KEY:
        raise SystemExit("PADDLE_API_KEY is not set. Export it, or use --dry-run.")

    live = "sandbox" not in API_BASE
    plans = load_plans()

    print(f"target : {API_BASE}  {'*** LIVE ***' if live else '(sandbox)'}")
    print(f"plans  : {len(plans)} paid  |  credit packs: {len(CREDIT_PACKS)}")
    print(f"prices : {len(plans) * 2 + len(CREDIT_PACKS)} total to ensure\n")

    if args.dry_run:
        for name, pm, py, credits in plans:
            print(f"  product  EvolvixOS {name}")
            print(f"    price  monthly  {CURRENCY} {pm:>7.2f}   ({credits} credits/mo)")
            print(f"    price  yearly   {CURRENCY} {py:>7.2f}")
        for credits, price in CREDIT_PACKS:
            print(f"  product  EvolvixOS {credits} Credits  (one-time)")
            print(f"    price  one-time {CURRENCY} {price:>7.2f}")
        print("\ndry run only, nothing created")
        return

    existing_products = {p["name"]: p for p in list_all("/products")}
    existing_prices = list_all("/prices")
    result = {"api_base": API_BASE, "currency": CURRENCY,
              "subscriptions": {}, "credits": {}}

    def ensure_product(name, description, tax_category="standard",
                       custom_data=None):
        if name in existing_products:
            pid = existing_products[name]["id"]
            print(f"  = product {name}  ({pid})")
            return pid
        body = {"name": name, "description": description,
                "tax_category": tax_category}
        if custom_data:
            body["custom_data"] = custom_data
        pid = api("POST", "/products", body)["data"]["id"]
        print(f"  + product {name}  ({pid})")
        return pid

    def ensure_price(product_id, amount, label, billing_cycle=None,
                     custom_data=None):
        minor = str(int(round(float(amount) * 100)))
        for pr in existing_prices:
            if (pr.get("product_id") == product_id
                    and pr.get("billing_cycle") == billing_cycle
                    and (pr.get("unit_price") or {}).get("amount") == minor):
                print(f"    = price {label:<9} {pr['id']}")
                return pr["id"]
        body = {"product_id": product_id, "description": label,
                "unit_price": {"amount": minor, "currency_code": CURRENCY},
                "billing_cycle": billing_cycle}
        if custom_data:
            body["custom_data"] = custom_data
        pid = api("POST", "/prices", body)["data"]["id"]
        print(f"    + price {label:<9} {pid}")
        return pid

    for name, pm, py, credits in plans:
        prod = ensure_product(
            f"EvolvixOS {name}",
            f"{name} plan - {credits} credits per month",
            custom_data={"plan": name, "credits_monthly": str(credits)})
        result["subscriptions"][f"{name}_monthly"] = ensure_price(
            prod, pm, "monthly", {"interval": "month", "frequency": 1},
            custom_data={"type": "subscription", "plan": name, "cycle": "monthly"})
        result["subscriptions"][f"{name}_yearly"] = ensure_price(
            prod, py, "yearly", {"interval": "year", "frequency": 1},
            custom_data={"type": "subscription", "plan": name, "cycle": "yearly"})

    for credits, price in CREDIT_PACKS:
        prod = ensure_product(
            f"EvolvixOS {credits} Credits",
            f"One-time top-up of {credits} EvolvixOS credits",
            custom_data={"credits": str(credits)})
        result["credits"][f"credits_{credits}"] = ensure_price(
            prod, price, "one-time", None,
            custom_data={"type": "credits", "credits": str(credits)})

    with open(OUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    total = len(result["subscriptions"]) + len(result["credits"])
    print(f"\n  {total} price ids written to {OUT_FILE}")
    print("  custom_data on each price carries type/plan/cycle/credits, which")
    print("  Paddle echoes back on transaction.completed for fulfilment.")


if __name__ == "__main__":
    main()
