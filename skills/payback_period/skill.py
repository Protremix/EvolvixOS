#!/usr/bin/env python3
"""Payback Period Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        investment = float(args.get("initial_investment", 10000.0))
        annual_cash_flow = float(args.get("annual_cash_flow", 2500.0))
        period = investment / annual_cash_flow if annual_cash_flow > 0 else None
        return {"initial_investment": investment, "payback_years": round(period, 2) if period else None}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
