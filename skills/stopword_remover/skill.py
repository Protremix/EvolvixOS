#!/usr/bin/env python3
"""Stopword Remover - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        stopwords = {"the", "a", "an", "is", "are", "and", "or", "in", "on", "at", "to", "for", "of", "with"}
        words = text.split()
        filtered = [w for w in words if w.lower() not in stopwords]
        return {"cleaned_text": " ".join(filtered)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
