#!/usr/bin/env python3
"""HTTP Headers Analyzer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        headers = args.get("headers", {"server": "nginx", "content-type": "text/html"})
        keys = [k.lower() for k in headers.keys()]
        sec_headers = ["strict-transport-security", "content-security-policy", "x-frame-options"]
        missing = [h for h in sec_headers if h not in keys]
        return {"headers_count": len(headers), "missing_security_headers": missing}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
