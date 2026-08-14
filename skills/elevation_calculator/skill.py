#!/usr/bin/env python3
"""Slope & Grade Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        elevation_change_m = float(args.get("elevation_change_m", 100.0))
        distance_m = float(args.get("horizontal_distance_m", 1000.0))
        grade_pct = (elevation_change_m / distance_m) * 100.0
        angle_deg = math.degrees(math.atan(elevation_change_m / distance_m))
        return {"grade_percentage": round(grade_pct, 2), "angle_degrees": round(angle_deg, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
