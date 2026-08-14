#!/usr/bin/env python3
"""Prime Factorizer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        n = int(args.get("n", 60))
        temp = n
        factors = []
        d = 2
        while temp > 1:
            while temp % d == 0:
                factors.append(d)
                temp //= d
            d += 1
            if d * d > temp:
                if temp > 1: factors.append(temp); break
        return {"n": n, "prime_factors": factors, "is_prime": len(factors) == 1}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
