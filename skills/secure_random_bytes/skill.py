#!/usr/bin/env python3
"""Secure Random Bytes - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import secrets
        count = int(args.get("count", 16))
        b = secrets.token_bytes(count)
        return {"hex": b.hex(), "bytes_len": len(b)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
