#!/usr/bin/env python3
"""IBAN Validator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        iban = args.get("iban", "").upper().replace(" ", "")
        if not iban:
            return {"error": "iban required"}
        if len(iban) < 15 or len(iban) > 34:
            return {"valid": False, "error": "Invalid length"}
        country = iban[:2]
        rearranged = iban[4:] + iban[:4]
        numeric = ""
        for c in rearranged:
            if c.isdigit():
                numeric += c
            elif c.isalpha():
                numeric += str(ord(c) - 55)
            else:
                return {"valid": False, "error": "Invalid character"}
        valid = int(numeric) % 97 == 1
        return {"valid": valid, "iban": iban, "country": country}
