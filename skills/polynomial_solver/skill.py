#!/usr/bin/env python3
"""Polynomial Solver - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import cmath
        a = float(args.get("a", 1.0))
        b = float(args.get("b", -5.0))
        c = float(args.get("c", 6.0))
        d = b**2 - 4*a*c
        r1 = (-b + cmath.sqrt(d)) / (2*a)
        r2 = (-b - cmath.sqrt(d)) / (2*a)
        return {"root1": str(r1), "root2": str(r2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
