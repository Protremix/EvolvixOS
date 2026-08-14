#!/usr/bin/env python3
"""Geographic Bounding Box - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        lat = float(args.get("lat", 37.7749))
        lon = float(args.get("lon", -122.4194))
        radius_km = float(args.get("radius_km", 10.0))
        lat_delta = radius_km / 111.0
        lon_delta = radius_km / (111.0 * 0.8) # approx
        return {
            "min_lat": round(lat - lat_delta, 4),
            "max_lat": round(lat + lat_delta, 4),
            "min_lon": round(lon - lon_delta, 4),
            "max_lon": round(lon + lon_delta, 4)
        }

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
