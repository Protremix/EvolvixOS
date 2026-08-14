#!/usr/bin/env python3
"""Midpoint Calculator — 100% Free, 100% Local"""
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
        bx = math.cos(lat2) * math.cos(dlon)
        by = math.cos(lat2) * math.sin(dlon)
        mid_lat = math.atan2(math.sin(lat1) + math.sin(lat2), math.sqrt((math.cos(lat1) + bx)**2 + by**2))
        mid_lon = lon1 + math.atan2(by, math.cos(lat1) + bx)
        return {"midpoint": {"lat": round(math.degrees(mid_lat), 6), "lon": round(math.degrees(mid_lon), 6)}}
