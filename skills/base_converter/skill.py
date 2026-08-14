#!/usr/bin/env python3
"""Base Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        value = args.get("value", "0")
        from_base = args.get("from_base", 10)
        to_base = args.get("to_base", 2)
        try:
            num = int(str(value), from_base) if from_base != 10 else int(value)
            if to_base == 2:
                result = bin(num)[2:]
            elif to_base == 8:
                result = oct(num)[8:]
            elif to_base == 16:
                result = hex(num)[2:].upper()
            elif to_base == 10:
                result = str(num)
            else:
                digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                if num == 0:
                    result = "0"
                else:
                    result = ""
                    n = abs(num)
                    while n > 0:
                        result = digits[n % to_base] + result
                        n //= to_base
                    if num < 0:
                        result = "-" + result
            return {"result": result, "decimal": num, "from_base": from_base, "to_base": to_base}
        except ValueError as e:
            return {"error": str(e)}
