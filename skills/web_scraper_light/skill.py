#!/usr/bin/env python3
"""Lightweight Web Scraper - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        html = args.get("html", "<html><head><title>Test</title></head><body><a href='http://x.com'>Link</a></body></html>")
        title_m = re.search(r'<title>(.*?)</title>', html, re.I)
        title = title_m.group(1) if title_m else ""
        links = re.findall(r'href=['"](.*?)['"]', html)
        return {"title": title, "links": links}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
