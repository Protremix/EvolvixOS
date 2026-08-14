#!/usr/bin/env python3
"""Duplicate File Finder - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os, hashlib, collections
        path = args.get("path", ".")
        by_size = collections.defaultdict(list)
        for root, _, files in os.walk(path):
            for f in files:
                p = os.path.join(root, f)
                try: by_size[os.path.getsize(p)].append(p)
                except Exception: pass
        dups = []
        for sz, file_list in by_size.items():
            if len(file_list) > 1 and sz > 0:
                hashes = collections.defaultdict(list)
                for fp in file_list:
                    try:
                        h = hashlib.sha256(open(fp, 'rb').read()).hexdigest()
                        hashes[h].append(fp)
                    except Exception: pass
                for h, h_files in hashes.items():
                    if len(h_files) > 1: dups.append(h_files)
        return {"duplicates": dups, "group_count": len(dups)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
