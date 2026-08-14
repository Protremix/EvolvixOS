#!/usr/bin/env python3
"""Color Mixer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        hex1 = args.get("hex1", "#FF0000").lstrip('#')
        hex2 = args.get("hex2", "#0000FF").lstrip('#')
        r1, g1, b1 = [int(hex1[i:i+2], 16) for i in (0, 2, 4)]
        r2, g2, b2 = [int(hex2[i:i+2], 16) for i in (0, 2, 4)]
        mr, mg, mb = (r1+r2)//2, (g1+g2)//2, (b1+b2)//2
        return {"mixed_hex": f"#{mr:02X}{mg:02X}{mb:02X}", "rgb": [mr, mg, mb]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
