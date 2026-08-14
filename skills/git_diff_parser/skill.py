#!/usr/bin/env python3
"""Git Diff Parser - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        diff = args.get("diff", "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-old\n+new")
        additions = sum(1 for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff.splitlines() if l.startswith("-") and not l.startswith("---"))
        return {"additions": additions, "deletions": deletions}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
