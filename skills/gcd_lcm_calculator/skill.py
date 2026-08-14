#!/usr/bin/env python3
"""GCD & LCM Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        a = int(args.get("a", 12))
        b = int(args.get("b", 18))
        gcd = math.gcd(a, b)
        lcm = (a * b) // gcd if gcd else 0
        return {"a": a, "b": b, "gcd": gcd, "lcm": lcm}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
