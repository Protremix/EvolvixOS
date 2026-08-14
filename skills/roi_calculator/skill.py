#!/usr/bin/env python3
"""ROI Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cost = float(args.get("initial_investment", 1000.0))
        gain = float(args.get("final_value", 1500.0))
        net = gain - cost
        roi = (net / cost) * 100.0
        return {"net_profit": round(net, 2), "roi_percent": round(roi, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
