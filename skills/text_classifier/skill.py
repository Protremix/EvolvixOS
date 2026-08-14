#!/usr/bin/env python3
"""Text Classifier - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "").lower()
        cats = args.get("categories", {"tech": ["code", "software", "api"], "sports": ["game", "score", "ball"]})
        scores = {cat: sum(text.count(w) for w in words) for cat, words in cats.items()}
        best = max(scores.items(), key=lambda x: x[1])[0] if any(scores.values()) else "unknown"
        return {"category": best, "scores": scores}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
