#!/usr/bin/env python3
"""GC Content Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        seq = args.get("dna", "ATGCGC").upper()
        gc_count = seq.count("G") + seq.count("C")
        pct = (gc_count / len(seq)) * 100 if seq else 0
        return {"length": len(seq), "gc_count": gc_count, "gc_percentage": round(pct, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
