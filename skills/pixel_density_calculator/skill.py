#!/usr/bin/env python3
"""Pixel Density (PPI) Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        w = float(args.get("width_px", 1920))
        h = float(args.get("height_px", 1080))
        diag = float(args.get("diagonal_inches", 15.6))
        ppi = math.sqrt(w**2 + h**2) / diag
        return {"ppi": round(ppi, 2), "diagonal_inches": diag}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
