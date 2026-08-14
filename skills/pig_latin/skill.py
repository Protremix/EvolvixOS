#!/usr/bin/env python3
"""Pig Latin Translator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        words = text.split()
        vowels = "aeiouAEIOU"
        res = []
        for w in words:
            if w[0] in vowels:
                res.append(w + "way")
            else:
                i = 0
                while i < len(w) and w[i] not in vowels: i += 1
                res.append(w[i:] + w[:i] + "ay")
        return {"result": " ".join(res)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
