#!/usr/bin/env python3
"""Cron Expression Parser — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        expr = args.get("expression", "*/5 * * * *")
        if not expr:
            return {"error": "expression required"}
        parts = expr.split()
        if len(parts) != 5:
            return {"error": "Cron must have 5 fields"}
        fields = ["minute", "hour", "day_of_month", "month", "day_of_week"]
        ranges = {"minute": (0, 59), "hour": (0, 23), "day_of_month": (1, 31), "month": (1, 12), "day_of_week": (0, 6)}
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        explanation = []
        for i, (field, value) in enumerate(zip(fields, parts)):
            field_desc = f"{field}: {value}"
            if value == "*":
                field_desc += f" (every {field.replace('_', ' ')})"
            elif "/" in value:
                base, step = value.split("/")
                field_desc += f" (every {step} {field.replace('_', ' '')}s)"
            elif "-" in value:
                start, end = value.split("-")
                field_desc += f" (from {start} to {end})"
            explanation.append(field_desc)
        return {"expression": expr, "fields": dict(zip(fields, parts)), "explanation": explanation}
