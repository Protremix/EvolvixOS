#!/usr/bin/env python3
"""Depreciation Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        cost = args.get("cost", 50000)
        salvage = args.get("salvage", 5000)
        life = args.get("life", 5)
        method = args.get("method", "straight")
        if method == "straight":
            annual = (cost - salvage) / life
            schedule = [{"year": y+1, "depreciation": annual, "book_value": cost - annual * (y+1)} for y in range(life)]
        elif method == "declining":
            rate = args.get("rate", 2) / life
            book = cost
            schedule = []
            for y in range(life):
                dep = book * rate
                if book - dep < salvage:
                    dep = book - salvage
                book -= dep
                schedule.append({"year": y+1, "depreciation": dep, "book_value": book})
        else:
            return {"error": f"Unknown method: {method}"}
        return {"method": method, "annual_depreciation": schedule[0]["depreciation"] if method == "straight" else None, "schedule": schedule}
