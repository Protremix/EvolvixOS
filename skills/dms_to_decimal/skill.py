#!/usr/bin/env python3
"""DMS to Decimal Degrees - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        d = float(args.get("degrees", 37))
        m = float(args.get("minutes", 46))
        s = float(args.get("seconds", 30))
        direction = args.get("direction", "N").upper()
        dd = d + m/60.0 + s/3600.0
        if direction in ["S", "W"]: dd = -dd
        return {"decimal_degrees": round(dd, 6)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
