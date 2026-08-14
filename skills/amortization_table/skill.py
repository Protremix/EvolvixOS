#!/usr/bin/env python3
"""Amortization Table Generator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        balance = float(args.get("principal", 1000.0))
        r = (float(args.get("rate_percent", 12.0)) / 100.0) / 12.0
        n = int(args.get("months", 6))
        m = balance * (r * (1 + r)**n) / ((1 + r)**n - 1)
        schedule = []
        for i in range(1, n + 1):
            interest = balance * r
            principal = m - interest
            balance -= principal
            schedule.append({"month": i, "payment": round(m, 2), "interest": round(interest, 2), "principal": round(principal, 2), "remaining_balance": round(max(0, balance), 2)})
        return {"schedule": schedule}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
