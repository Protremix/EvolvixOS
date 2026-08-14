#!/usr/bin/env python3
"""Dividend Yield Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        annual_dividend = float(args.get("annual_dividend_per_share", 3.50))
        stock_price = float(args.get("stock_price", 100.0))
        yld = (annual_dividend / stock_price) * 100.0
        return {"dividend_yield_percent": round(yld, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
