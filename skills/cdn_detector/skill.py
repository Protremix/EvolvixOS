#!/usr/bin/env python3
"""CDN Detector - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        headers = args.get("headers", {"cf-ray": "123456"})
        cdn = "Unknown"
        h_lower = {k.lower(): v for k, v in headers.items()}
        if "cf-ray" in h_lower: cdn = "Cloudflare"
        elif "x-amz-cf-id" in h_lower: cdn = "Amazon CloudFront"
        elif "fastly-debug" in h_lower: cdn = "Fastly"
        return {"cdn": cdn}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
