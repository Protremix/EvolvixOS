#!/usr/bin/env python3
"""Astronomy Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        ly = float(args.get("light_years", 1.0))
        km = ly * 9.461e12
        au = ly * 63241.1
        return {"light_years": ly, "km": km, "AU": round(au, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
