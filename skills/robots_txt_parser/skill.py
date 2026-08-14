#!/usr/bin/env python3
"""Robots.txt Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        content = args.get("content", "User-agent: *\nDisallow: /admin")
        disallowed = []
        for line in content.splitlines():
            if line.lower().startswith("disallow:"):
                disallowed.append(line.split(":", 1)[1].strip())
        return {"disallowed_paths": disallowed}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
