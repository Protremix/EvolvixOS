#!/usr/bin/env python3
"""Anagram Finder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import collections
        word1 = args.get("word1", "")
        word2 = args.get("word2", "")
        c1 = collections.Counter(word1.lower().replace(" ", ""))
        c2 = collections.Counter(word2.lower().replace(" ", ""))
        return {"is_anagram": c1 == c2, "word1": word1, "word2": word2}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
