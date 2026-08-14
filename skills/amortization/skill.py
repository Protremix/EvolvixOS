#!/usr/bin/env python3
"""Amortization Table — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        principal = args.get("principal", 200000)
        rate = args.get("rate", 6) / 100 / 12
        months = args.get("months", 360)
        if rate == 0:
            payment = principal / months
        else:
            payment = principal * (rate * (1 + rate)**months) / ((1 + rate)**months - 1)
        balance = principal
        schedule = []
        for m in range(1, months + 1):
            interest = balance * rate
            principal_payment = payment - interest
            balance -= principal_payment
            schedule.append({"month": m, "payment": round(payment, 2), "interest": round(interest, 2), "principal": round(principal_payment, 2), "balance": round(max(0, balance), 2)})
            if balance <= 0:
                break
        return {"monthly_payment": round(payment, 2), "total_interest": round(sum(s["interest"] for s in schedule), 2), "total_paid": round(payment * len(schedule), 2), "schedule": schedule}
