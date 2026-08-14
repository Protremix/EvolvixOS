#!/usr/bin/env python3
"""Response Generator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        template = args.get("template", "Hello!")
        variables = args.get("variables", {})
        if not template:
            return {"error": "template required"}
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return {"response": result, "template": template, "variables": variables}
