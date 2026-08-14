#!/usr/bin/env python3
"""Color Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import colorsys
        hex_color = args.get("hex", "#FF5733").lstrip('#')
        r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
        h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        return {"rgb": [r, g, b], "hsv": [round(h*360, 1), round(s*100, 1), round(v*100, 1)], "hex": f"#{hex_color}"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
