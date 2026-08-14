#!/usr/bin/env python3
"""Domain Extractor - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import urllib.parse
        url = args.get("url", "https://sub.example.co.uk/path")
        host = urllib.parse.urlparse(url).netloc or url
        parts = host.split(".")
        tld = ".".join(parts[-2:]) if len(parts) >= 2 else host
        return {"hostname": host, "domain": tld}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
