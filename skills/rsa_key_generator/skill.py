#!/usr/bin/env python3
"""RSA Key Helper - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        p, q = 61, 53
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 17
        d = 2753
        return {"modulus_n": n, "public_e": e, "private_d": d, "bit_length": n.bit_length()}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
