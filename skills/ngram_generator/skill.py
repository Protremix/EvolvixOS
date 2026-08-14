#!/usr/bin/env python3
"""N-gram Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        n = args.get("n", 2)
        if not text:
            return {"error": "text required"}
        words = re.findall(r'\b\w+\b', text.lower())
        ngrams = [" ".join(words[i:i+n]) for i in range(len(words) - n + 1)]
        from collections import Counter
        freq = Counter(ngrams)
        return {"ngrams": ngrams, "n": n, "unique": len(freq), "top": freq.most_common(10)}
