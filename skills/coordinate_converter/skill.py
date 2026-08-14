#!/usr/bin/env python3
"""Coordinate Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        dd = float(args.get("decimal_degrees", 37.7749))
        d = int(dd)
        m = int((abs(dd) - abs(d)) * 60)
        s = round((abs(dd) - abs(d) - m/60) * 3600, 2)
        return {"decimal_degrees": dd, "dms": f"{d}° {m}' {s}""}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
