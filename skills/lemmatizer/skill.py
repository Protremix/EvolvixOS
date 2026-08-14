#!/usr/bin/env python3
"""Lemmatizer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        word = args.get("word", "running").lower()
        mapping = {"running": "run", "better": "good", "cats": "cat", "studies": "study"}
        lemma = mapping.get(word, word.rstrip("s") if word.endswith("s") and len(word) > 3 else word)
        return {"word": word, "lemma": lemma}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
