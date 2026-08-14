#!/usr/bin/env python3
"""Destination Point Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        lat = math.radians(float(args.get("lat", 37.7749)))
        lon = math.radians(float(args.get("lon", -122.4194)))
        bearing = math.radians(float(args.get("bearing_deg", 90.0)))
        dist = float(args.get("distance_km", 100.0))
        R = 6371.0
        lat2 = math.asin(math.sin(lat)*math.cos(dist/R) + math.cos(lat)*math.sin(dist/R)*math.cos(bearing))
        lon2 = lon + math.atan2(math.sin(bearing)*math.sin(dist/R)*math.cos(lat), math.cos(dist/R)-math.sin(lat)*math.sin(lat2))
        return {"dest_lat": round(math.degrees(lat2), 4), "dest_lon": round(math.degrees(lon2), 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
