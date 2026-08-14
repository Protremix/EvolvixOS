#!/usr/bin/env python3
"""Inflation Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        amount = float(args.get("amount", 100.0))
        inflation_rate = float(args.get("rate_percent", 3.0)) / 100.0
        years = float(args.get("years", 10.0))
        future_amount = amount * ((1 + inflation_rate) ** years)
        return {"current_amount": amount, "future_equivalent": round(future_amount, 2), "years": years}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
