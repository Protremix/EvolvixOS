#!/usr/bin/env python3
"""Password Strength Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math, string
        pwd = args.get("password", "")
        pool = 0
        if any(c in string.ascii_lowercase for c in pwd): pool += 26
        if any(c in string.ascii_uppercase for c in pwd): pool += 26
        if any(c in string.digits for c in pwd): pool += 10
        if any(c in string.punctuation for c in pwd): pool += 32
        entropy = len(pwd) * math.log2(pool) if pool and pwd else 0
        score = "weak"
        if entropy > 60: score = "very strong"
        elif entropy > 45: score = "strong"
        elif entropy > 28: score = "moderate"
        return {"entropy_bits": round(entropy, 2), "score": score, "length": len(pwd)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
