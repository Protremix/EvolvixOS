#!/usr/bin/env python3
"""Unicode Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        code_points = [f"U+{ord(c):04X}" for c in text]
        hex_bytes = text.encode('utf-8').hex()
        html_entities = "".join([f"&#{ord(c)};" for c in text])
        return {"code_points": code_points, "hex_bytes": hex_bytes, "html_entities": html_entities}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
