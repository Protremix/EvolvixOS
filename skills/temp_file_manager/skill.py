#!/usr/bin/env python3
"""Temp File Manager - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import tempfile, os
        content = args.get("content", "Hello Temp")
        suffix = args.get("suffix", ".tmp")
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name
        return {"temp_path": temp_path, "exists": os.path.exists(temp_path), "size": len(content)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
