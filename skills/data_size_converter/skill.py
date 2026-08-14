#!/usr/bin/env python3
"""Data Size Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        value = args.get("value", 1024)
        from_unit = args.get("from", "B")
        to_unit = args.get("to", "KB")
        units = {"bit": 0.125, "B": 1, "KB": 1024, "MB": 1048576, "GB": 1073741824, "TB": 1099511627776, "PB": 1125899906842624}
        if from_unit not in units or to_unit not in units:
            return {"error": "invalid unit"}
        value_in_bytes = value * units[from_unit]
        result = value_in_bytes / units[to_unit]
        return {"result": round(result, 6), "value": value, "from": from_unit, "to": to_unit}
