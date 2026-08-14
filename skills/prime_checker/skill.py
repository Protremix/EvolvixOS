#!/usr/bin/env python3
"""Prime Number Checker — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        num = args.get("number", 2)
        if num < 2:
            return {"is_prime": False, "number": num, "reason": "Less than 2"}
        if num == 2:
            return {"is_prime": True, "number": num}
        if num % 2 == 0:
            return {"is_prime": False, "number": num, "reason": "Even number > 2"}
        for i in range(3, int(math.isqrt(num)) + 1, 2):
            if num % i == 0:
                return {"is_prime": False, "number": num, "factor": i}
        return {"is_prime": True, "number": num}
