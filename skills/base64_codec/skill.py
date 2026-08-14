#!/usr/bin/env python3
"""Base64 Encoder/Decoder — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import base64
        text = args.get("text", "")
        action = args.get("action", "encode")
        if not text:
            return {"error": "text required"}
        if action == "encode":
            encoded = base64.b64encode(text.encode()).decode()
            return {"encoded": encoded, "original": text}
        elif action == "decode":
            try:
                decoded = base64.b64decode(text).decode()
                return {"decoded": decoded, "encoded": text}
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"unknown action: {action}"}
