#!/usr/bin/env python3
"""File Finder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os, fnmatch
        path = args.get("path", ".")
        pattern = args.get("pattern", "*")
        matches = []
        for root, dirs, files in os.walk(path):
            for f in fnmatch.filter(files, pattern):
                matches.append(os.path.join(root, f))
                if len(matches) >= 100: break
            if len(matches) >= 100: break
        return {"matches": matches, "count": len(matches)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
