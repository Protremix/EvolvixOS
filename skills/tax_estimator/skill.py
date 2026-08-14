#!/usr/bin/env python3
"""Tax Estimator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        income = float(args.get("income", 75000.0))
        deduction = 13850.0
        taxable = max(0.0, income - deduction)
        # Simple brackets estimation
        tax = taxable * 0.15
        return {"gross_income": income, "taxable_income": taxable, "estimated_tax": round(tax, 2), "effective_rate_percent": round((tax/income)*100, 2) if income else 0}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
