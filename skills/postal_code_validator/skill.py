#!/usr/bin/env python3
"""Postal Code Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        code = args.get("code", "90210")
        country = args.get("country", "US").upper()
        patterns = {"US": r'^\d{5}(-\d{4})?$', "UK": r'^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$', "CA": r'^[A-Z]\d[A-Z] \d[A-Z]\d$'}
        pat = patterns.get(country, r'^[A-Za-z0-9 -]{3,10}$')
        valid = bool(re.match(pat, code))
        return {"code": code, "country": country, "is_valid": valid}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
