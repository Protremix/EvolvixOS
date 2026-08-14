#!/usr/bin/env python3
"""File Comparator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import difflib
        file1 = args.get("file1", "")
        file2 = args.get("file2", "")
        diff = list(difflib.unified_diff(file1.splitlines(), file2.splitlines(), lineterm=""))
        return {"identical": file1 == file2, "diff": diff}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
