#!/usr/bin/env python3
"""cURL Command Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        url = args.get("url", "https://api.example.com/data")
        method = args.get("method", "GET").upper()
        headers = args.get("headers", {})
        body = args.get("body", "")
        parts = [f"curl -X {method} '{url}'"]
        for k, v in headers.items(): parts.append(f"-H '{k}: {v}'")
        if body: parts.append(f"-d '{body}'")
        return {"command": " ".join(parts)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
