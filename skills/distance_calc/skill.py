#!/usr/bin/env python3
"""Distance Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        lat1 = args.get("lat1", 0)
        lon1 = args.get("lon1", 0)
        lat2 = args.get("lat2", 0)
        lon2 = args.get("lon2", 0)
        unit = args.get("unit", "km")
        R = 6371 if unit == "km" else 3959
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        return {"distance": round(distance, 2), "unit": unit, "from": {"lat": lat1, "lon": lon1}, "to": {"lat": lat2, "lon": lon2}}
