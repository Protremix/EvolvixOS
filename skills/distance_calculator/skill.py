#!/usr/bin/env python3
"""Haversine Distance Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        lat1 = float(args.get("lat1", 37.7749))
        lon1 = float(args.get("lon1", -122.4194))
        lat2 = float(args.get("lat2", 34.0522))
        lon2 = float(args.get("lon2", -118.2437))
        R = 6371.0 # Earth radius km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        km = R * c
        return {"distance_km": round(km, 2), "distance_miles": round(km * 0.621371, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
