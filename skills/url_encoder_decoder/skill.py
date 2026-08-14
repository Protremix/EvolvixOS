#!/usr/bin/env python3
"""URL Encoder/Decoder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import urllib.parse
        text = args.get("text", "")
        action = args.get("action", "encode")
        if action == "encode":
            return {"result": urllib.parse.quote(text)}
        else:
            return {"result": urllib.parse.unquote(text)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
