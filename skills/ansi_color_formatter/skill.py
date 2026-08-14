#!/usr/bin/env python3
"""ANSI Terminal Color Formatter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "Hello World")
        color = args.get("color", "red").lower()
        CODES = {"red": "[31m", "green": "[32m", "blue": "[34m", "yellow": "[33m"}
        c_code = CODES.get(color, "[31m")
        return {"formatted_text": f"{c_code}{text}[0m"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
