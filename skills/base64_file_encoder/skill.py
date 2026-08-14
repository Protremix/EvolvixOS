#!/usr/bin/env python3
"""Base64 File Encoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64
        data = args.get("data", "")
        action = args.get("action", "encode")
        if action == "encode":
            return {"b64": base64.b64encode(data.encode('utf-8')).decode('utf-8')}
        else:
            return {"decoded": base64.b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
