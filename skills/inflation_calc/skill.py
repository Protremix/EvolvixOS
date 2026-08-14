#!/usr/bin/env python3
"""Inflation Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        amount = args.get("amount", 100)
        rate = args.get("rate", 3) / 100
        years = args.get("years", 10)
        future = amount * (1 + rate) ** years
        equivalent = amount / (1 + rate) ** years
        return {"current_amount": amount, "future_value": round(future, 2), "real_value": round(equivalent, 2), "purchasing_power_loss": round((1 - equivalent / amount) * 100, 2), "rate": rate * 100, "years": years}
