#!/usr/bin/env python3
"""Nautical Miles Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        nmi = float(args.get("nautical_miles", 10.0))
        km = nmi * 1.852
        mi = nmi * 1.15078
        return {"nautical_miles": nmi, "km": round(km, 2), "statute_miles": round(mi, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
