#!/usr/bin/env python3
"""Working Capital Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        assets = float(args.get("current_assets", 150000.0))
        liab = float(args.get("current_liabilities", 90000.0))
        wc = assets - liab
        ratio = assets / liab if liab else 0
        return {"working_capital": wc, "current_ratio": round(ratio, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
