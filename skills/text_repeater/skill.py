#!/usr/bin/env python3
"""Text Repeater - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        count = int(args.get("count", 3))
        delimiter = args.get("delimiter", " ")
        res = delimiter.join([text] * count)
        return {"result": res, "count": count}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
