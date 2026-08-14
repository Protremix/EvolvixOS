#!/usr/bin/env python3
"""Credit Card Validator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        number = args.get("number", "")
        number = re.sub(r'[\s-]', '', number)
        if not number.isdigit():
            return {"valid": False, "error": "Invalid format"}
        total = 0
        for i, digit in enumerate(reversed(number)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        valid = total % 10 == 0
        card_types = {"4": "Visa", "5": "Mastercard", "3": "Amex", "6": "Discover"}
        card_type = card_types.get(number[0], "Unknown") if number else "Unknown"
        return {"valid": valid, "number": number, "card_type": card_type, "luhn_check": total % 10 == 0}
