#!/usr/bin/env python3
"""Vector Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        v1 = args.get("v1", [1, 2, 3])
        v2 = args.get("v2", [4, 5, 6])
        dot = sum(a * b for a, b in zip(v1, v2))
        mag1 = math.sqrt(sum(a**2 for a in v1))
        mag2 = math.sqrt(sum(b**2 for b in v2))
        return {"dot_product": dot, "magnitude_v1": round(mag1, 4), "magnitude_v2": round(mag2, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
