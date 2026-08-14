#!/usr/bin/env python3
"""XOR Cipher - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        key = args.get("key", "K")
        out = "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
        return {"result": out}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
