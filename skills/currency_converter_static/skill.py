#!/usr/bin/env python3
"""Currency Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        amount = float(args.get("amount", 100.0))
        from_c = args.get("from", "USD").upper()
        to_c = args.get("to", "EUR").upper()
        RATES = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "CAD": 1.35}
        val_usd = amount / RATES.get(from_c, 1.0)
        converted = val_usd * RATES.get(to_c, 1.0)
        return {"amount": amount, "from": from_c, "to": to_c, "converted": round(converted, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
