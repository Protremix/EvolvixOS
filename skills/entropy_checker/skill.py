#!/usr/bin/env python3
"""Entropy Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math, collections
        text = args.get("text", "")
        if not text: return {"entropy": 0.0}
        counts = collections.Counter(text)
        length = len(text)
        entropy = -sum((c / length) * math.log2(c / length) for c in counts.values())
        return {"entropy": round(entropy, 4), "length": length}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
