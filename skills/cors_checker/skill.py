#!/usr/bin/env python3
"""CORS Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        headers = args.get("headers", {"access-control-allow-origin": "*"})
        origin = headers.get("access-control-allow-origin", "None")
        return {"allow_origin": origin, "wildcard_allowed": origin == "*"}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
