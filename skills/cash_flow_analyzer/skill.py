#!/usr/bin/env python3
"""Cash Flow Analyzer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        inflows = sum(args.get("inflows", [5000, 3000, 2000]))
        outflows = sum(args.get("outflows", [2000, 1500, 1000]))
        net = inflows - outflows
        return {"total_inflows": inflows, "total_outflows": outflows, "net_cash_flow": net}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
