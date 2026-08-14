#!/usr/bin/env python3
"""Decibel (dB) Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        p1 = float(args.get("p1", 1.0))
        p2 = float(args.get("p2", 100.0))
        db = 10 * math.log10(p2 / p1)
        return {"p1": p1, "p2": p2, "dB": round(db, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
