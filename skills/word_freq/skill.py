#!/usr/bin/env python3
"""Word Frequency Analyzer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        from collections import Counter
        text = args.get("text", "")
        top_n = args.get("top", 20)
        if not text:
            return {"error": "text required"}
        words = re.findall(r'\b\w+\b', text.lower())
        freq = Counter(words)
        total = len(words)
        unique = len(freq)
        return {"total_words": total, "unique_words": unique, "top": [{"word": w, "count": c, "percentage": round(c / total * 100, 2)} for w, c in freq.most_common(top_n)], "lexical_diversity": round(unique / total, 4) if total > 0 else 0}
