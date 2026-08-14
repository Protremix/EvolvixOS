#!/usr/bin/env python3
"""Porter Stemmer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        word = args.get("word", "connecting").lower()
        suffixes = ["ing", "ed", "ly", "es", "s", "ment"]
        stem = word
        for s in suffixes:
            if word.endswith(s) and len(word) > len(s) + 2:
                stem = word[:-len(s)]; break
        return {"word": word, "stem": stem}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
