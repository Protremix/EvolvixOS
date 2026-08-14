#!/usr/bin/env python3
"""File Metadata Reader — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import os, time, hashlib
        path = args.get("file", "")
        if not path or not os.path.exists(path):
            return {"error": "file required"}
        stat = os.stat(path)
        return {
            "path": path,
            "size": stat.st_size,
            "size_human": f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / 1048576:.1f} MB",
            "modified": time.ctime(stat.st_mtime),
            "created": time.ctime(stat.st_ctime),
            "accessed": time.ctime(stat.st_atime),
            "mode": oct(stat.st_mode),
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "is_link": os.path.islink(path),
            "extension": os.path.splitext(path)[1],
        }
