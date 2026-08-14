#!/usr/bin/env python3
"""Directory Tree Printer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os
        path = args.get("path", ".")
        max_depth = int(args.get("max_depth", 2))
        lines = [path]
        def build_tree(dir_path, prefix="", depth=0):
            if depth >= max_depth: return
            try:
                entries = sorted(os.listdir(dir_path))
            except Exception: return
            for i, e in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{e}")
                full = os.path.join(dir_path, e)
                if os.path.isdir(full):
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    build_tree(full, new_prefix, depth + 1)
        build_tree(path)
        return {"tree": "\n".join(lines)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
