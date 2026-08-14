#!/usr/bin/env python3
"""Date Formatter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        from datetime import datetime
        date_str = args.get("date", "")
        input_fmt = args.get("input_format", "%Y-%m-%d")
        output_fmt = args.get("output_format", "%B %d, %Y")
        if not date_str:
            date_str = datetime.now().strftime(input_fmt)
        try:
            dt = datetime.strptime(date_str, input_fmt)
            return {"formatted": dt.strftime(output_fmt), "original": date_str, "iso": dt.isoformat(), "weekday": dt.strftime("%A")}
        except ValueError as e:
            return {"error": str(e)}
