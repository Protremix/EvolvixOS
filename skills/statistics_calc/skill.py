#!/usr/bin/env python3
"""Statistics Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        data = args.get("data", [])
        if not data:
            return {"error": "data required"}
        n = len(data)
        mean = sum(data) / n
        variance = sum((x - mean)**2 for x in data) / n
        std = math.sqrt(variance)
        sorted_data = sorted(data)
        if n % 2 == 0:
            median = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
        else:
            median = sorted_data[n//2]
        from collections import Counter
        freq = Counter(data)
        mode = freq.most_common(1)[0][0] if freq else None
        q1 = sorted_data[n//4]
        q3 = sorted_data[3*n//4]
        return {
            "count": n,
            "mean": round(mean, 6),
            "median": median,
            "mode": mode,
            "range": max(data) - min(data),
            "variance": round(variance, 6),
            "std_dev": round(std, 6),
            "min": min(data),
            "max": max(data),
            "sum": sum(data),
            "q1": q1,
            "q3": q3,
            "iqr": q3 - q1,
        }
