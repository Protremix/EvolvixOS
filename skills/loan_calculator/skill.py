#!/usr/bin/env python3
"""Loan Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        p = float(args.get("principal", 10000.0))
        rate_annual = float(args.get("rate_percent", 5.0)) / 100.0
        years = int(args.get("years", 3))
        n = years * 12
        r = rate_annual / 12.0
        m = p * (r * (1 + r)**n) / ((1 + r)**n - 1) if r else p / n
        total = m * n
        return {"monthly_payment": round(m, 2), "total_payment": round(total, 2), "total_interest": round(total - p, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
