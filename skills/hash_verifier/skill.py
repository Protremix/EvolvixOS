#!/usr/bin/env python3
"""Hash Verifier - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import hashlib, hmac
        text = args.get("text", "")
        target = args.get("hash", "").lower()
        algo = args.get("algo", "sha256")
        h = hashlib.new(algo, text.encode('utf-8')).hexdigest().lower()
        return {"matches": hmac.compare_digest(h, target), "computed": h}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
