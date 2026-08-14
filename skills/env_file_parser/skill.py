#!/usr/bin/env python3
"""Dotenv File Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        content = args.get("content", "PORT=8080\nDB_HOST=localhost\nDB_PASS=secret123")
        res = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            if "=" in line:
                k, v = line.split("=", 1)
                res[k.strip()] = v.strip().strip('"\'')
        return {"env": res}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
