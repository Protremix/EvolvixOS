#!/usr/bin/env python3
"""Radioactive Decay Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        n0 = float(args.get("initial_mass", 100.0))
        half_life = float(args.get("half_life_years", 5.0))
        time_y = float(args.get("time_years", 10.0))
        remaining = n0 * (0.5 ** (time_y / half_life))
        return {"initial_mass": n0, "remaining_mass": round(remaining, 4), "time_years": time_y}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
