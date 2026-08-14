#!/usr/bin/env python3
"""Location Radius Filter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        center_lat = float(args.get("center_lat", 37.7749))
        center_lon = float(args.get("center_lon", -122.4194))
        radius_km = float(args.get("radius_km", 50.0))
        locations = args.get("locations", [{"name": "Close", "lat": 37.8, "lon": -122.4}, {"name": "Far", "lat": 40.0, "lon": -120.0}])
        filtered = [loc for loc in locations if abs(loc["lat"] - center_lat) * 111 < radius_km]
        return {"matching_locations": filtered, "count": len(filtered)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
