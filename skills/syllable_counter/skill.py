#!/usr/bin/env python3
"""Syllable Counter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        words = re.findall(r'\b[a-zA-Z]+\b', text)
        def count_syllables(w):
            w = w.lower()
            if len(w) <= 3: return 1
            w = re.sub(r'(?:[^laeiouy]es|[^laeiouy]e)$', '', w)
            m = re.findall(r'[aeiouy]{1,2}', w)
            return max(1, len(m))
        word_details = [{"word": w, "syllables": count_syllables(w)} for w in words]
        total = sum(d["syllables"] for d in word_details)
        return {"total_syllables": total, "word_count": len(words), "details": word_details[:20]}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
