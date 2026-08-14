#!/usr/bin/env python3
"""Electronics Calculator (Ohm's Law) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        v = args.get("voltage")
        i = args.get("current")
        r = args.get("resistance")
        if v is None and i is not None and r is not None:
            v = float(i) * float(r)
        elif i is None and v is not None and r is not None:
            i = float(v) / float(r)
        elif r is None and v is not None and i is not None:
            r = float(v) / float(i)
        power = (float(v) * float(i)) if v and i else None
        return {"voltage": v, "current": i, "resistance": r, "power_W": power}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
