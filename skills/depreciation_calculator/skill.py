#!/usr/bin/env python3
"""Depreciation Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cost = float(args.get("asset_cost", 10000.0))
        salvage = float(args.get("salvage_value", 1000.0))
        life = int(args.get("useful_life_years", 5))
        annual = (cost - salvage) / life
        schedule = [{"year": i, "depreciation": round(annual, 2), "ending_book_value": round(cost - annual * i, 2)} for i in range(1, life + 1)]
        return {"annual_depreciation": round(annual, 2), "schedule": schedule}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
