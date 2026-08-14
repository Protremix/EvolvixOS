#!/usr/bin/env python3
"""Bearing Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        lat1 = math.radians(args.get("lat1", 0))
        lon1 = math.radians(args.get("lon1", 0))
        lat2 = math.radians(args.get("lat2", 0))
        lon2 = math.radians(args.get("lon2", 0))
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = math.degrees(math.atan2(x, y))
        bearing = (bearing + 360) % 360
        dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        direction = dirs[int(round(bearing / 45) % 8)]
        return {"bearing": round(bearing, 2), "direction": direction}
