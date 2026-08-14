#!/usr/bin/env python3
"""Markup Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cost = float(args.get("cost", 50.0))
        markup_pct = float(args.get("markup_percent", 40.0))
        price = cost * (1 + markup_pct / 100.0)
        profit = price - cost
        return {"selling_price": round(price, 2), "gross_profit": round(profit, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
