#!/usr/bin/env python3
"""Text Reverser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        mode = args.get("mode", "chars")
        if mode == "words":
            res = " ".join(text.split()[::-1])
        elif mode == "lines":
            res = "\n".join(text.splitlines()[::-1])
        else:
            res = text[::-1]
        return {"result": res, "mode": mode}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
