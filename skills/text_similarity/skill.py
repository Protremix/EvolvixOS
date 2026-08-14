#!/usr/bin/env python3
"""Text Similarity Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        t1 = set(args.get("text1", "").lower().split())
        t2 = set(args.get("text2", "").lower().split())
        jaccard = len(t1 & t2) / max(1, len(t1 | t2))
        return {"jaccard_similarity": round(jaccard, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
