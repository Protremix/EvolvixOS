#!/usr/bin/env python3
"""Cosine Similarity Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        v1 = args.get("v1", [1, 1, 0])
        v2 = args.get("v2", [1, 0, 1])
        dot = sum(a * b for a, b in zip(v1, v2))
        m1 = math.sqrt(sum(a**2 for a in v1))
        m2 = math.sqrt(sum(b**2 for b in v2))
        cos_sim = dot / (m1 * m2) if (m1 * m2) else 0
        return {"cosine_similarity": round(cos_sim, 4)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
