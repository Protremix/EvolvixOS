#!/usr/bin/env python3
"""Sentiment Analyzer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "").lower()
        pos = ["good", "great", "excellent", "awesome", "happy", "love"]
        neg = ["bad", "terrible", "awful", "sad", "hate", "poor"]
        p_count = sum(text.count(w) for w in pos)
        n_count = sum(text.count(w) for w in neg)
        compound = (p_count - n_count) / max(1, p_count + n_count)
        label = "positive" if compound > 0.1 else ("negative" if compound < -0.1 else "neutral")
        return {"compound_score": round(compound, 2), "sentiment": label}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
