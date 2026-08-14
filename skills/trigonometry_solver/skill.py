#!/usr/bin/env python3
"""Trigonometry Right-Triangle Solver - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        a = float(args.get("side_a", 3.0))
        b = float(args.get("side_b", 4.0))
        c = math.sqrt(a**2 + b**2)
        angle_A = math.degrees(math.atan(a / b))
        return {"side_a": a, "side_b": b, "hypotenuse_c": c, "angle_A_deg": round(angle_A, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
