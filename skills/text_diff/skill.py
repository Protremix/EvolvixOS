#!/usr/bin/env python3
"""Text Diff - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import difflib
        text1 = args.get("text1", "")
        text2 = args.get("text2", "")
        diff = list(difflib.ndiff(text1.splitlines(), text2.splitlines()))
        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        return {"diff": diff, "similarity_ratio": round(ratio, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
