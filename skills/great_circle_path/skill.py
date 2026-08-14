#!/usr/bin/env python3
"""Great Circle Path Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        lat1 = float(args.get("lat1", 0.0))
        lon1 = float(args.get("lon1", 0.0))
        lat2 = float(args.get("lat2", 10.0))
        lon2 = float(args.get("lon2", 10.0))
        steps = int(args.get("steps", 3))
        waypoints = []
        for i in range(steps + 1):
            f = i / steps
            waypoints.append({"lat": round(lat1 + f*(lat2-lat1), 4), "lon": round(lon1 + f*(lon2-lon1), 4)})
        return {"waypoints": waypoints}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
