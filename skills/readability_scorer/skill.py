#!/usr/bin/env python3
"""Readability Scorer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        if not text:
            return {"error": "text is required"}
        sentences = max(1, len([s for s in re.split(r'[.!?]+', text) if s.strip()]))
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        word_count = max(1, len(words))
        def count_syllables(word):
            word = word.lower()
            if len(word) <= 3: return 1
            word = re.sub(r'(?:[^laeiouy]es|[^laeiouy]e)$', '', word)
            return max(1, len(re.findall(r'[aeiouy]{1,2}', word)))
        syllables = sum(count_syllables(w) for w in words)
        flesch = 206.835 - (1.015 * (word_count / sentences)) - (84.6 * (syllables / word_count))
        grade = (0.39 * (word_count / sentences)) + (11.8 * (syllables / word_count)) - 15.59
        return {"flesch_reading_ease": round(flesch, 2), "flesch_kincaid_grade": round(grade, 2), "words": word_count, "sentences": sentences, "syllables": syllables}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
