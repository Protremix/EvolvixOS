#!/usr/bin/env python3
"""HTTP Client - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import urllib.request, json
        url = args.get("url", "https://httpbin.org/get")
        method = args.get("method", "GET").upper()
        headers = args.get("headers", {})
        data = args.get("data")
        req_body = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode('utf-8')
                return {"status": resp.status, "body": body[:500]}
        except Exception as e:
            return {"error": str(e)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
