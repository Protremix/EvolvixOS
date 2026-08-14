#!/usr/bin/env python3
"""Geographic Midpoint Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        lat1 = float(args.get("lat1", 37.7749))
        lon1 = float(args.get("lon1", -122.4194))
        lat2 = float(args.get("lat2", 34.0522))
        lon2 = float(args.get("lon2", -118.2437))
        return {"mid_lat": round((lat1 + lat2)/2, 4), "mid_lon": round((lon1 + lon2)/2, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
