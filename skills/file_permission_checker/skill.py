#!/usr/bin/env python3
"""File Permission Checker - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import os
        path = args.get("path", ".")
        exists = os.path.exists(path)
        readable = os.access(path, os.R_OK) if exists else False
        writable = os.access(path, os.W_OK) if exists else False
        executable = os.access(path, os.X_OK) if exists else False
        return {"path": path, "exists": exists, "readable": readable, "writable": writable, "executable": executable}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
