#!/usr/bin/env python3
"""Luma Brightness Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        rgb = args.get("rgb", [255, 255, 255])
        r, g, b = rgb
        y = 0.299*r + 0.587*g + 0.114*b
        return {"rgb": rgb, "luminance": round(y, 2), "is_light": y > 128}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
