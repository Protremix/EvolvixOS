#!/usr/bin/env python3
"""Sales Tax Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        price = float(args.get("subtotal", 50.0))
        tax_rate = float(args.get("tax_rate_percent", 8.25))
        tax = price * (tax_rate / 100.0)
        return {"subtotal": price, "tax_amount": round(tax, 2), "total": round(price + tax, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
