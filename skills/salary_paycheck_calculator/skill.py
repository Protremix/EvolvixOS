#!/usr/bin/env python3
"""Paycheck Estimator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        gross = float(args.get("gross_pay", 2500.0))
        tax = gross * 0.22
        net = gross - tax
        return {"gross_pay": gross, "estimated_taxes": round(tax, 2), "net_take_home": round(net, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
