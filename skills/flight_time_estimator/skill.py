#!/usr/bin/env python3
"""Flight Time Estimator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        dist_km = float(args.get("distance_km", 4000.0))
        cruise_kmh = 850.0
        flight_hours = (dist_km / cruise_kmh) + 0.5 # plus taxi/climb
        return {"distance_km": dist_km, "estimated_flight_hours": round(flight_hours, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
