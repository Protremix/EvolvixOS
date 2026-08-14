#!/usr/bin/env python3
"""String Formatter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        template = args.get("template", "")
        values = args.get("values", {})
        if not template:
            return {"error": "template required"}
        try:
            result = template.format(**values)
            return {"result": result}
        except (KeyError, IndexError) as e:
            return {"error": f"Missing key: {e}"}
        except Exception as e:
            return {"error": str(e)}
