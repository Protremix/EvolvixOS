#!/usr/bin/env python3
"""Keyword Extractor - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re, collections
        text = args.get("text", "")
        top_n = int(args.get("top_n", 5))
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {"the", "and", "that", "this", "with", "from", "for", "are"}
        filtered = [w for w in words if w not in stopwords]
        counts = collections.Counter(filtered)
        return {"keywords": [w for w, _ in counts.most_common(top_n)]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
