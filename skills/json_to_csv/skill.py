#!/usr/bin/env python3
"""JSON to CSV - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import csv, io
        data = args.get("data", [])
        if not data or not isinstance(data, list): return {"csv": ""}
        fieldnames = list(data[0].keys())
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        return {"csv": out.getvalue()}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
