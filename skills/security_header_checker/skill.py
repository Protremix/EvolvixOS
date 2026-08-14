#!/usr/bin/env python3
"""Security Header Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        headers = args.get("headers", {})
        h_lower = {k.lower(): v for k, v in headers.items()}
        required = ["strict-transport-security", "content-security-policy", "x-frame-options", "x-content-type-options"]
        missing = [r for r in required if r not in h_lower]
        return {"missing_headers": missing, "score": f"{len(required)-len(missing)}/{len(required)}"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
