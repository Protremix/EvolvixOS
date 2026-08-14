#!/usr/bin/env python3
"""Bearing Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        lat1 = math.radians(float(args.get("lat1", 37.7749)))
        lon1 = math.radians(float(args.get("lon1", -122.4194)))
        lat2 = math.radians(float(args.get("lat2", 34.0522)))
        lon2 = math.radians(float(args.get("lon2", -118.2437)))
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
        return {"bearing_degrees": round(bearing, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
