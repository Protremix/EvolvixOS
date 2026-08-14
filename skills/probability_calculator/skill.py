#!/usr/bin/env python3
"""Probability Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        n = int(args.get("n", 5))
        r = int(args.get("r", 2))
        nCr = math.comb(n, r)
        nPr = math.perm(n, r)
        return {"n": n, "r": r, "combinations_nCr": nCr, "permutations_nPr": nPr}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
