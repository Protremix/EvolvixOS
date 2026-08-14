#!/usr/bin/env python3
"""Duplicate File Finder — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import os, hashlib
        path = args.get("path", ".")
        hashes = {}
        duplicates = {}
        for root, dirs, files in os.walk(path):
            for f in files:
                full = os.path.join(root, f)
                try:
                    h = hashlib.md5()
                    with open(full, "rb") as fh:
                        h.update(fh.read())
                    digest = h.hexdigest()
                    if digest in hashes:
                        if digest not in duplicates:
                            duplicates[digest] = [hashes[digest]]
                        duplicates[digest].append(full)
                    else:
                        hashes[digest] = full
                except (PermissionError, OSError):
                    pass
        return {"duplicates": duplicates, "duplicate_groups": len(duplicates), "wasted_space": sum(os.path.getsize(v[1]) for v in duplicates.values() if len(v) > 1)}
