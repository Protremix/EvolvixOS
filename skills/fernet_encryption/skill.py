#!/usr/bin/env python3
"""Symmetric Cipher Helper - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64
        key = args.get("key", "secret_key").encode('utf-8')
        text = args.get("text", "hello").encode('utf-8')
        action = args.get("action", "encrypt")
        if action == "encrypt":
            cipher = bytes([b ^ key[i % len(key)] for i, b in enumerate(text)])
            return {"cipher_b64": base64.b64encode(cipher).decode('utf-8')}
        else:
            raw = base64.b64decode(text.decode('utf-8') if isinstance(text, bytes) else text)
            plain = bytes([b ^ key[i % len(key)] for i, b in enumerate(raw)])
            return {"plain": plain.decode('utf-8', errors='ignore')}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
