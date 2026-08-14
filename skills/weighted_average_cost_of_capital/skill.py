#!/usr/bin/env python3
"""WACC Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        E = float(args.get("equity", 600000))
        D = float(args.get("debt", 400000))
        Re = float(args.get("cost_of_equity_percent", 10.0)) / 100.0
        Rd = float(args.get("cost_of_debt_percent", 5.0)) / 100.0
        T = float(args.get("tax_rate_percent", 21.0)) / 100.0
        V = E + D
        wacc = (E / V) * Re + (D / V) * Rd * (1 - T)
        return {"wacc_percent": round(wacc * 100, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
