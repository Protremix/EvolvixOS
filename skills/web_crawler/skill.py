#!/usr/bin/env python3
"""Web Crawler Skill - Crawl4AI (Apache 2.0) - 100% Free"""
import json, sys, subprocess, os


class Skill:
    """Scrape any website into clean text. Free, local, no API keys."""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        url = args.get("url", "")
        if not url:
            return {"error": "url required"}
        try:
            import requests
            r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            return {"url": url, "content": r.text[:50000], "chars": len(r.text), "status": r.status_code}
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
