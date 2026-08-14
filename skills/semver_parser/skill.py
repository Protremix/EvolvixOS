#!/usr/bin/env python3
"""SemVer Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        version = args.get("version", "1.2.3-beta.1")
        m = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?', version)
        if m:
            return {"major": int(m.group(1)), "minor": int(m.group(2)), "patch": int(m.group(3)), "prerelease": m.group(4)}
        return {"error": "not a valid semver"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
