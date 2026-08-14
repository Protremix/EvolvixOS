#!/usr/bin/env python3
"""Caesar Cipher - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        shift = int(args.get("shift", 3))
        action = args.get("action", "encrypt")
        if action == "decrypt": shift = -shift
        res = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                res.append(chr((ord(c) - base + shift) % 26 + base))
            else:
                res.append(c)
        return {"result": "".join(res), "shift": shift}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
