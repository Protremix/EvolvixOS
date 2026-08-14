#!/usr/bin/env python3
"""ISBN Validator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        isbn = args.get("isbn", "").replace("-", "").replace(" ", "")
        if not isbn:
            return {"error": "isbn required"}
        if len(isbn) == 10:
            total = sum((10 - i) * (int(c) if c.isdigit() else 10) for i, c in enumerate(isbn))
            return {"valid": total % 11 == 0, "isbn": isbn, "type": "ISBN-10"}
        elif len(isbn) == 13:
            total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(isbn))
            return {"valid": total % 10 == 0, "isbn": isbn, "type": "ISBN-13"}
        else:
            return {"valid": False, "error": "Invalid length"}
