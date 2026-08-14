#!/usr/bin/env python3
"""Password Strength Checker — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import re
        password = args.get("password", "")
        if not password:
            return {"error": "password required"}
        score = 0
        feedback = []
        if len(password) >= 8: score += 1
        else: feedback.append("Use at least 8 characters")
        if len(password) >= 12: score += 1
        else: feedback.append("Use 12+ characters for stronger security")
        if re.search(r'[A-Z]', password): score += 1
        else: feedback.append("Add uppercase letters")
        if re.search(r'[a-z]', password): score += 1
        else: feedback.append("Add lowercase letters")
        if re.search(r'\d', password): score += 1
        else: feedback.append("Add numbers")
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password): score += 1
        else: feedback.append("Add special characters")
        if len(set(password)) < len(password) * 0.5: feedback.append("Avoid repeated characters")
        import math
        charset = 0
        if re.search(r'[a-z]', password): charset += 26
        if re.search(r'[A-Z]', password): charset += 26
        if re.search(r'\d', password): charset += 10
        if re.search(r'[^a-zA-Z0-9]', password): charset += 32
        entropy = round(len(password) * math.log2(max(charset, 1)), 1)
        levels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Good", 5: "Strong", 6: "Very Strong", 7: "Excellent"}
        return {"score": score, "max_score": 7, "level": levels.get(score, "Unknown"), "entropy_bits": entropy, "feedback": feedback, "length": len(password)}
