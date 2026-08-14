#!/usr/bin/env python3
"""JWT Decoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64, json
        token = args.get("token", "")
        parts = token.split(".")
        if len(parts) < 2: return {"error": "invalid jwt format"}
        def b64_decode(s):
            s += '=' * (-len(s) % 4)
            return json.loads(base64.urlsafe_b64decode(s).decode('utf-8'))
        try:
            header = b64_decode(parts[0])
            payload = b64_decode(parts[1])
            return {"header": header, "payload": payload}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
