#!/usr/bin/env python3
"""User-Agent Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        ua = args.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0.0.0 Safari/537.36")
        browser = "Unknown"
        if "Chrome" in ua: browser = "Chrome"
        elif "Firefox" in ua: browser = "Firefox"
        elif "Safari" in ua: browser = "Safari"
        os_name = "Unknown"
        if "Windows" in ua: os_name = "Windows"
        elif "Macintosh" in ua: os_name = "macOS"
        elif "Linux" in ua: os_name = "Linux"
        return {"user_agent": ua, "browser": browser, "os": os_name}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
