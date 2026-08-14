#!/usr/bin/env python3
"""Mortgage Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        p = float(args.get("home_price", 300000.0))
        down = float(args.get("down_payment", 60000.0))
        loan = p - down
        rate = float(args.get("rate_percent", 6.5)) / 100.0 / 12.0
        n = int(args.get("years", 30)) * 12
        m = loan * (rate * (1 + rate)**n) / ((1 + rate)**n - 1)
        return {"loan_amount": loan, "monthly_pi": round(m, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
