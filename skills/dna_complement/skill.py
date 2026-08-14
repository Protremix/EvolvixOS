#!/usr/bin/env python3
"""DNA Complement - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        seq = args.get("dna", "ATCG").upper()
        comp = {"A": "T", "T": "A", "C": "G", "G": "C"}
        complement = "".join([comp.get(b, b) for b in seq])
        rna = seq.replace("T", "U")
        return {"dna": seq, "complement": complement, "reverse_complement": complement[::-1], "rna": rna}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
