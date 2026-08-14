#!/usr/bin/env python3
"""Rule of 72 Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        rate = float(args.get("interest_rate_percent", 6.0))
        years = 72.0 / rate if rate else 0
        return {"rate_percent": rate, "doubling_time_years": round(years, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
