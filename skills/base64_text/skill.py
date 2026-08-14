#!/usr/bin/env python3
"""Base64 Text Encoder/Decoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import base64
        action = args.get("action", "encode")
        text = args.get("text", "")
        try:
            if action == "encode":
                res = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                return {"result": res, "action": "encode"}
            elif action == "decode":
                res = base64.b64decode(text.encode('utf-8')).decode('utf-8')
                return {"result": res, "action": "decode"}
            return {"error": f"unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
