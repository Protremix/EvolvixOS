#!/usr/bin/env python3
"""Internal Rate of Return (IRR) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cash_flows = args.get("cash_flows", [-1000, 300, 400, 500, 600])
        # Simple Newton-Raphson approximation for IRR
        r = 0.1
        for _ in range(20):
            npv = sum(cf / ((1 + r) ** i) for i, cf in enumerate(cash_flows))
            d_npv = sum(-i * cf / ((1 + r) ** (i + 1)) for i, cf in enumerate(cash_flows))
            if abs(d_npv) < 1e-6: break
            r = r - npv / d_npv
        return {"estimated_irr_percent": round(r * 100, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
