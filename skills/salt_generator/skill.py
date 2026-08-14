#!/usr/bin/env python3
"""Salt Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import secrets, base64
        nbytes = int(args.get("nbytes", 16))
        salt = secrets.token_bytes(nbytes)
        return {"salt_hex": salt.hex(), "salt_b64": base64.b64encode(salt).decode('utf-8')}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
