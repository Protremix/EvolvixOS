#!/usr/bin/env python3
"""CSV Deduplicator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import csv, io
        csv_text = args.get("csv", "")
        key_col = args.get("key_column")
        reader = csv.DictReader(io.StringIO(csv_text))
        seen = set()
        unique = []
        for r in reader:
            k = r.get(key_col) if key_col else tuple(r.items())
            if k not in seen:
                seen.add(k)
                unique.append(r)
        if unique:
            out = io.StringIO()
            w = csv.DictWriter(out, fieldnames=list(unique[0].keys()))
            w.writeheader()
            w.writerows(unique)
            return {"csv": out.getvalue(), "removed_count": len(list(csv.DictReader(io.StringIO(csv_text)))) - len(unique)}
        return {"csv": "", "removed_count": 0}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
