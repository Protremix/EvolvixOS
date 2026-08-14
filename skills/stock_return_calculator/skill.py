#!/usr/bin/env python3
"""Stock Return & CAGR Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        buy_price = float(args.get("purchase_price", 100.0))
        sell_price = float(args.get("current_price", 150.0))
        years = float(args.get("years", 3.0))
        total_return = ((sell_price - buy_price) / buy_price) * 100.0
        cagr = ((sell_price / buy_price) ** (1 / years) - 1) * 100.0
        return {"total_return_percent": round(total_return, 2), "cagr_percent": round(cagr, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
