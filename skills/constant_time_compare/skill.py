#!/usr/bin/env python3
"""Constant-Time String Compare - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import hmac
        val1 = args.get("val1", "")
        val2 = args.get("val2", "")
        return {"equal": hmac.compare_digest(val1, val2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
