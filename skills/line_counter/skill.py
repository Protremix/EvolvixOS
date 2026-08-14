#!/usr/bin/env python3
"""Line Counter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        lines = text.splitlines()
        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comment = sum(1 for l in lines if l.strip().startswith("#"))
        code = total - blank - comment
        return {"total_lines": total, "blank_lines": blank, "comment_lines": comment, "code_lines": code}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
