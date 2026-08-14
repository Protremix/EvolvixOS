#!/usr/bin/env python3
"""Collatz Sequence — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        n = args.get("number", 27)
        if n <= 0:
            return {"error": "number must be positive"}
        sequence = [n]
        steps = 0
        while n != 1:
            if n % 2 == 0:
                n = n // 2
            else:
                n = 3 * n + 1
            sequence.append(n)
            steps += 1
            if steps > 10000:
                return {"sequence": sequence, "steps": steps, "error": "Too many steps"}
        return {"sequence": sequence, "steps": steps, "max_value": max(sequence)}
