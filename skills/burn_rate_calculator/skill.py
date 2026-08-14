#!/usr/bin/env python3
"""Burn Rate & Runway Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cash = float(args.get("cash_balance", 200000.0))
        expenses = float(args.get("monthly_expenses", 30000.0))
        revenue = float(args.get("monthly_revenue", 10000.0))
        net_burn = expenses - revenue
        runway = cash / net_burn if net_burn > 0 else 999.0
        return {"net_burn_rate": net_burn, "runway_months": round(runway, 1)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
