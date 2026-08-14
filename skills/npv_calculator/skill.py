#!/usr/bin/env python3
"""NPV Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        rate = float(args.get("rate", 0.1))
        cash_flows = args.get("cash_flows", [-1000, 300, 400, 500, 600])
        npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
        return {"npv": round(npv, 2), "discount_rate": rate}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
