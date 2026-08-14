#!/usr/bin/env python3
"""Speed Distance Time Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        d = args.get("distance_km")
        s = args.get("speed_kmh")
        t = args.get("time_hours")
        if d is None and s and t: d = float(s) * float(t)
        elif s is None and d and t: s = float(d) / float(t)
        elif t is None and d and s: t = float(d) / float(s)
        return {"distance_km": d, "speed_kmh": s, "time_hours": t}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
