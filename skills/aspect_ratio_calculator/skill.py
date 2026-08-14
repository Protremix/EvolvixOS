#!/usr/bin/env python3
"""Aspect Ratio Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        w = int(args.get("width", 1920))
        h = int(args.get("height", 1080))
        gcd = math.gcd(w, h)
        return {"width": w, "height": h, "aspect_ratio": f"{w//gcd}:{h//gcd}"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
