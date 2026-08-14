#!/usr/bin/env python3
"""Time Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        value = args.get("value", 0)
        from_unit = args.get("from", "seconds")
        to_unit = args.get("to", "minutes")
        units = {"nanoseconds": 1e-9, "microseconds": 1e-6, "milliseconds": 0.001, "seconds": 1, "minutes": 60, "hours": 3600, "days": 86400, "weeks": 604800, "months": 2629800, "years": 31557600}
        if from_unit not in units or to_unit not in units:
            return {"error": "invalid unit"}
        value_in_seconds = value * units[from_unit]
        result = value_in_seconds / units[to_unit]
        return {"result": round(result, 10), "value": value, "from": from_unit, "to": to_unit}
