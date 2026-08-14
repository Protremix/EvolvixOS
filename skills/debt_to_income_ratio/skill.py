#!/usr/bin/env python3
"""Debt-to-Income (DTI) Ratio - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        debts = float(args.get("monthly_debt_payments", 1500.0))
        income = float(args.get("gross_monthly_income", 5000.0))
        dti = (debts / income) * 100.0
        return {"dti_percent": round(dti, 2), "status": "Good" if dti < 36 else "High"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
