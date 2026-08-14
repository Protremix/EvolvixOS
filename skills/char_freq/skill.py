#!/usr/bin/env python3
"""Character Frequency Analyzer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        from collections import Counter
        text = args.get("text", "")
        if not text:
            return {"error": "text required"}
        chars = Counter(text)
        letters = Counter(c for c in text if c.isalpha())
        digits = Counter(c for c in text if c.isdigit())
        spaces = text.count(" ")
        return {"total_chars": len(text), "unique_chars": len(chars), "letters": sum(letters.values()), "digits": sum(digits.values()), "spaces": spaces, "top_chars": chars.most_common(10), "letter_distribution": dict(letters.most_common(26))}
