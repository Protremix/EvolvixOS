#!/usr/bin/env python3
"""Git Log Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        log_text = args.get("log", "commit 1234abcd\nAuthor: John Doe <john@doe.com>\nDate: Fri Aug 14 12:00:00 2026\n\n    Initial commit")
        commits = []
        curr = {}
        for line in log_text.splitlines():
            if line.startswith("commit "):
                if curr: commits.append(curr); curr = {}
                curr["hash"] = line.split()[1]
            elif line.startswith("Author: "):
                curr["author"] = line.replace("Author: ", "").strip()
            elif line.startswith("Date: "):
                curr["date"] = line.replace("Date: ", "").strip()
            elif line.strip() and curr:
                curr["message"] = curr.get("message", "") + line.strip() + " "
        if curr: commits.append(curr)
        return {"commits": commits, "count": len(commits)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
