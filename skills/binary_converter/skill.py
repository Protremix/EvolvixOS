#!/usr/bin/env python3
"""Binary Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        value = args.get("value", "0")
        from_base = args.get("from", "decimal")
        to_base = args.get("to", "binary")
        bases = {"binary": 2, "octal": 8, "decimal": 10, "hex": 16}
        try:
            if from_base == "decimal":
                num = int(value)
            else:
                num = int(str(value), bases[from_base])
            if to_base == "binary":
                result = bin(num)
            elif to_base == "octal":
                result = oct(num)
            elif to_base == "hex":
                result = hex(num)
            elif to_base == "decimal":
                result = str(num)
            else:
                result = str(num)
            return {"result": result, "decimal": num, "from": from_base, "to": to_base}
        except ValueError as e:
            return {"error": str(e)}
