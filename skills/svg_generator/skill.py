#!/usr/bin/env python3
"""SVG Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        w = int(args.get("width", 100))
        h = int(args.get("height", 100))
        svg = f'<svg width="{w}" height="{h}"><circle cx="{w//2}" cy="{h//2}" r="{w//3}" fill="red"/></svg>'
        return {"svg": svg}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
