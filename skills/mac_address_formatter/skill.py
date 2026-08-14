#!/usr/bin/env python3
"""MAC Address Formatter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        mac = args.get("mac", "001122334455")
        clean = re.sub(r'[^a-fA-F0-9]', '', mac).upper()
        if len(clean) != 12: return {"error": "invalid MAC length"}
        colon = ":".join([clean[i:i+2] for i in range(0, 12, 2)])
        dash = "-".join([clean[i:i+2] for i in range(0, 12, 2)])
        dot = ".".join([clean[i:i+4] for i in range(0, 12, 4)])
        return {"colon": colon, "dash": dash, "dot": dot}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
