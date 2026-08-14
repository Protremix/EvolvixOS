#!/usr/bin/env python3
"""Password Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import secrets, string
        length = int(args.get("length", 16))
        use_symbols = args.get("symbols", True)
        chars = string.ascii_letters + string.digits
        if use_symbols: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        pwd = "".join(secrets.choice(chars) for _ in range(length))
        return {"password": pwd, "length": length}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
