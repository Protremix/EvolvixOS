#!/usr/bin/env python3
"""Phone Number Validator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re
        phone = args.get("phone", "")
        digits = re.sub(r'\D', '', phone)
        valid = 10 <= len(digits) <= 15
        return {"phone": phone, "digits": digits, "is_valid": valid}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
