#!/usr/bin/env python3
"""Rhyme Finder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        word = args.get("word", "").lower()
        candidates = args.get("candidates", ["cat", "hat", "bat", "dog", "fog", "sing", "ring", "rat"])
        suffix = word[-2:] if len(word) >= 2 else word
        rhymes = [c for c in candidates if c.lower().endswith(suffix) and c.lower() != word]
        return {"word": word, "rhymes": rhymes}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
