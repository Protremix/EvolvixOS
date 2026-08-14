#!/usr/bin/env python3
"""CSV Merger - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import csv, io
        csv_list = args.get("csv_list", [])
        all_rows = []
        fieldnames = set()
        for c in csv_list:
            r = csv.DictReader(io.StringIO(c))
            for row in r:
                all_rows.append(row)
                fieldnames.update(row.keys())
        out = io.StringIO()
        w = csv.DictWriter(out, fieldnames=list(fieldnames))
        w.writeheader()
        w.writerows(all_rows)
        return {"csv": out.getvalue(), "total_rows": len(all_rows)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
