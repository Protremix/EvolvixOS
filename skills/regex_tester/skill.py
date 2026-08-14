#!/usr/bin/env python3
"""Regex Tester - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        pattern = args.get("pattern", "")
        text = args.get("text", "")
        if not pattern or text is None:
            return {"error": "pattern and text required"}
        try:
            regex = re.compile(pattern)
            matches = []
            for m in regex.finditer(text):
                matches.append({"match": m.group(0), "span": m.span(), "groups": m.groups()})
            return {"matches": matches, "match_count": len(matches), "is_valid": True}
        except Exception as e:
            return {"is_valid": False, "error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
