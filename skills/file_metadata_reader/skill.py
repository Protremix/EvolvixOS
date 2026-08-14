#!/usr/bin/env python3
"""File Metadata Reader - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os, datetime
        path = args.get("path", ".")
        if not os.path.exists(path): return {"error": "path does not exist"}
        st = os.stat(path)
        return {
            "path": path,
            "size_bytes": st.st_size,
            "is_dir": os.path.isdir(path),
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(),
            "mode": oct(st.st_mode)
        }

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
