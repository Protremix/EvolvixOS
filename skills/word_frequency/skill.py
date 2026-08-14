#!/usr/bin/env python3
"""Word Frequency Counter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import collections, re
        text = args.get("text", "")
        words = re.findall(r'\b\w+\b', text.lower())
        return {"frequencies": dict(collections.Counter(words).most_common(20))}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
