#!/usr/bin/env python3
"""Leetspeak Converter — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        leetspeak_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7", "l": "1", "b": "8", "g": "9", "A": "4", "E": "3", "I": "1", "O": "0", "S": "5", "T": "7", "L": "1"}
        result = "".join(leetspeak_map.get(c, c) for c in text)
        return {"leetspeak": result, "original": text}
