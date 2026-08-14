#!/usr/bin/env python3
"""Palindrome Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        text = args.get("text", "")
        cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
        is_pal = cleaned == cleaned[::-1] if cleaned else False
        return {"text": text, "cleaned": cleaned, "is_palindrome": is_pal}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
