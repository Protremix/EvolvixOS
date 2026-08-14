#!/usr/bin/env python3
"""HMAC Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import hmac, hashlib
        key = args.get("key", "secret").encode('utf-8')
        msg = args.get("message", "hello").encode('utf-8')
        algo = args.get("algo", "sha256")
        h = hmac.new(key, msg, getattr(hashlib, algo)).hexdigest()
        return {"hmac": h, "algo": algo}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
