#!/usr/bin/env python3
"""CAC Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        spend = float(args.get("sales_marketing_spend", 10000.0))
        new_cust = int(args.get("new_customers", 200))
        cac = spend / new_cust if new_cust else 0
        return {"cac": round(cac, 2), "new_customers": new_cust}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
