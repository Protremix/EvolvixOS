#!/usr/bin/env python3
"""Tip & Split Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        bill = float(args.get("bill_amount", 80.0))
        tip_pct = float(args.get("tip_percent", 18.0))
        people = int(args.get("people_count", 2))
        tip_amount = bill * (tip_pct / 100.0)
        total = bill + tip_amount
        per_person = total / people
        return {"tip_amount": round(tip_amount, 2), "total_bill": round(total, 2), "per_person": round(per_person, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
