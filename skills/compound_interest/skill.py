#!/usr/bin/env python3
"""Compound Interest Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        p = float(args.get("principal", 1000.0))
        r = float(args.get("rate_percent", 7.0)) / 100.0
        t = float(args.get("years", 10.0))
        n = int(args.get("compounds_per_year", 12))
        a = p * ((1 + r/n) ** (n * t))
        return {"future_value": round(a, 2), "interest_earned": round(a - p, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
