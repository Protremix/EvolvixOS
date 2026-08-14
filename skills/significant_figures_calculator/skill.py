#!/usr/bin/env python3
"""Significant Figures Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        val = float(args.get("value", 123.456))
        sf = int(args.get("sig_figs", 3))
        if val == 0: return {"result": 0.0}
        rounded = round(val, sf - int(math.floor(math.log10(abs(val)))) - 1)
        return {"value": val, "sig_figs": sf, "rounded": rounded}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
