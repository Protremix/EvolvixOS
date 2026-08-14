#!/usr/bin/env python3
"""Directory Tree Printer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import os
        path = args.get("path", ".")
        max_depth = args.get("max_depth", 3)
        def tree(p, prefix="", depth=0):
            if depth >= max_depth:
                return []
            result = []
            try:
                items = sorted(os.listdir(p))
            except PermissionError:
                return result
            for i, item in enumerate(items):
                full = os.path.join(p, item)
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                result.append(prefix + connector + item + ("/" if os.path.isdir(full) else ""))
                if os.path.isdir(full):
                    extension = "    " if is_last else "│   "
                    result.extend(tree(full, prefix + extension, depth + 1))
            return result
        lines = [path + "/"] + tree(path)
        return {"tree": "\n".join(lines), "lines": len(lines)}
