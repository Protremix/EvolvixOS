#!/usr/bin/env python3
"""Map Scale Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        map_dist_cm = float(args.get("map_distance_cm", 5.0))
        scale = float(args.get("scale_denominator", 50000.0))
        ground_m = (map_dist_cm * scale) / 100.0
        return {"map_distance_cm": map_dist_cm, "scale": f"1:{int(scale)}", "ground_distance_m": ground_m, "ground_distance_km": ground_m / 1000.0}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
