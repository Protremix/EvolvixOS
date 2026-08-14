#!/usr/bin/env python3
"""Temperature Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        value = args.get("value", 0)
        from_unit = args.get("from", "C")
        to_unit = args.get("to", "F")
        if from_unit == to_unit:
            result = value
        elif from_unit == "C" and to_unit == "F":
            result = value * 9/5 + 32
        elif from_unit == "F" and to_unit == "C":
            result = (value - 32) * 5/9
        elif from_unit == "C" and to_unit == "K":
            result = value + 273.15
        elif from_unit == "K" and to_unit == "C":
            result = value - 273.15
        elif from_unit == "F" and to_unit == "K":
            result = (value - 32) * 5/9 + 273.15
        elif from_unit == "K" and to_unit == "F":
            result = (value - 273.15) * 9/5 + 32
        else:
            return {"error": f"unknown units: {from_unit} -> {to_unit}"}
        return {"result": round(result, 2), "value": value, "from": from_unit, "to": to_unit}
