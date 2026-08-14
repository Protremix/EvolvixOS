#!/usr/bin/env python3
"""JSON Formatter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import json
        data = args.get("data")
        text = args.get("text")
        indent = args.get("indent", 2)
        try:
            obj = data if data is not None else json.loads(text)
            formatted = json.dumps(obj, indent=indent, sort_keys=True)
            return {"formatted": formatted, "valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
