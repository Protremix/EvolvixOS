#!/usr/bin/env python3
"""N-Gram Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        n = int(args.get("n", 2))
        words = text.split()
        ngrams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
        return {"ngrams": ngrams, "n": n}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
