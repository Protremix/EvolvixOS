#!/usr/bin/env python3
"""Base32 Encoder/Decoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64
        text = args.get("text", "")
        action = args.get("action", "encode")
        if action == "encode":
            return {"result": base64.b32encode(text.encode('utf-8')).decode('utf-8')}
        else:
            return {"result": base64.b32decode(text.encode('utf-8')).decode('utf-8', errors='ignore')}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
