#!/usr/bin/env python3
"""Vigenere Cipher - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        key = args.get("key", "KEY").upper()
        action = args.get("action", "encrypt")
        if not key: return {"error": "key is required"}
        res = []
        k_idx = 0
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                k_shift = ord(key[k_idx % len(key)]) - ord('A')
                if action == "decrypt": k_shift = -k_shift
                res.append(chr((ord(c) - base + k_shift) % 26 + base))
                k_idx += 1
            else:
                res.append(c)
        return {"result": "".join(res)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
