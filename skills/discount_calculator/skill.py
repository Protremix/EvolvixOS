#!/usr/bin/env python3
"""Discount Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        original = float(args.get("original_price", 100.0))
        discount_pct = float(args.get("discount_percent", 20.0))
        savings = original * (discount_pct / 100.0)
        final_price = original - savings
        return {"original_price": original, "savings": round(savings, 2), "final_price": round(final_price, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
