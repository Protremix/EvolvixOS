#!/usr/bin/env python3
"""TSV Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import csv, io
        tsv_text = args.get("tsv", "")
        r = csv.DictReader(io.StringIO(tsv_text), delimiter='\t')
        rows = list(r)
        return {"rows": rows, "count": len(rows)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
