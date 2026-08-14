#!/usr/bin/env python3
"""REST API Tester - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import urllib.request
        url = args.get("url", "https://httpbin.org/get")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return {"status": resp.status, "content_type": resp.headers.get("Content-Type")}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
