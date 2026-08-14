#!/usr/bin/env python3
"""CSRF Token Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import secrets, hmac, hashlib, time
        secret = args.get("secret", "csrf_secret").encode('utf-8')
        nonce = secrets.token_hex(16)
        ts = str(int(time.time()))
        msg = f"{nonce}:{ts}".encode('utf-8')
        sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
        return {"token": f"{nonce}:{ts}:{sig}"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
