#!/usr/bin/env python3
"""Percentage Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "of")
        x = args.get("x", 0)
        y = args.get("y", 0)
        if action == "of":
            result = (x / 100) * y
            return {"result": result, "description": f"{x}% of {y} = {result}"}
        elif action == "is_what":
            result = (x / y) * 100 if y != 0 else 0
            return {"result": round(result, 2), "description": f"{x} is {result}% of {y}"}
        elif action == "change":
            result = ((y - x) / x) * 100 if x != 0 else 0
            return {"result": round(result, 2), "description": f"Change from {x} to {y} = {result}%"}
        elif action == "increase":
            result = x * (1 + y / 100)
            return {"result": result, "description": f"{x} increased by {y}% = {result}"}
        elif action == "decrease":
            result = x * (1 - y / 100)
            return {"result": result, "description": f"{x} decreased by {y}% = {result}"}
        return {"error": f"unknown: {action}"}
