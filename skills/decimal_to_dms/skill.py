#!/usr/bin/env python3
"""Decimal Degrees to DMS - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        dd = float(args.get("decimal_degrees", 37.775))
        abs_dd = abs(dd)
        d = int(abs_dd)
        m = int((abs_dd - d) * 60)
        s = round((abs_dd - d - m/60.0) * 3600, 2)
        return {"degrees": d, "minutes": m, "seconds": s}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
