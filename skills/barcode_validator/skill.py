#!/usr/bin/env python3
"""Barcode Validator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        code = args.get("code", "")
        digits = re.sub(r'\D', '', code)
        if not digits:
            return {"error": "code required"}
        if len(digits) in (8, 12, 13, 14):
            total = sum(int(d) * (3 if i % 2 == 1 else 1) for i, d in enumerate(digits[:-1]))
            if len(digits) == 12:
                total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits[:-1]))
            check = (10 - total % 10) % 10
            valid = check == int(digits[-1])
            return {"valid": valid, "code": digits, "check_digit": int(digits[-1]), "expected_check": check, "type": f"{'EAN' if len(digits) == 13 else 'UPC'}-{len(digits)}"}
        return {"valid": False, "error": "Invalid barcode length"}
