#!/usr/bin/env python3
"""3D Coordinate Transform - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        x = float(args.get("x", 1.0))
        y = float(args.get("y", 1.0))
        z = float(args.get("z", 1.0))
        r = math.sqrt(x**2 + y**2 + z**2)
        theta = math.acos(z / r) if r else 0
        phi = math.atan2(y, x)
        return {"r": round(r, 4), "theta_rad": round(theta, 4), "phi_rad": round(phi, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
