#!/usr/bin/env python3
"""JSON Path Evaluator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        data = args.get("data", {})
        path = args.get("path", "")
        curr = data
        for part in path.split("."):
            if not part: continue
            if isinstance(curr, dict): curr = curr.get(part)
            elif isinstance(curr, list) and part.isdigit():
                idx = int(part)
                curr = curr[idx] if idx < len(curr) else None
            else:
                curr = None; break
        return {"path": path, "value": curr}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
