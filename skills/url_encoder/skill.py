#!/usr/bin/env python3
"""URL Encoder/Decoder — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        from urllib.parse import quote, unquote
        text = args.get("text", "")
        action = args.get("action", "encode")
        if not text:
            return {"error": "text required"}
        if action == "encode":
            return {"encoded": quote(text, safe=""), "original": text}
        elif action == "decode":
            return {"decoded": unquote(text), "original": text}
        return {"error": f"unknown: {action}"}
