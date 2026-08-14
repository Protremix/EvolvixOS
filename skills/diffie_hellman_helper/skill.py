#!/usr/bin/env python3
"""Diffie-Hellman Key Exchange Helper - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        p = int(args.get("p", 23))
        g = int(args.get("g", 5))
        a = int(args.get("private_key", 6))
        A = pow(g, a, p)
        return {"public_key": A, "p": p, "g": g}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
