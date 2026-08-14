#!/usr/bin/env python3
"""Hashtag Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re, collections
        text = args.get("text", "")
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        stopwords = {"the", "and", "for", "that", "this", "with", "from", "your", "have", "are"}
        filtered = [w.capitalize() for w in words if w.lower() not in stopwords]
        counts = collections.Counter(filtered)
        top = [f"#{w}" for w, _ in counts.most_common(10)]
        return {"hashtags": top, "count": len(top)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
