#!/usr/bin/env python3
"""Break-Even Analyzer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        fixed = args.get("fixed_costs", 10000)
        price = args.get("price", 50)
        variable = args.get("variable_cost", 30)
        if price <= variable:
            return {"error": "Price must exceed variable cost"}
        contribution = price - variable
        units = fixed / contribution
        revenue = units * price
        return {"break_even_units": round(units, 0), "break_even_revenue": round(revenue, 2), "contribution_margin": contribution, "fixed_costs": fixed, "price": price, "variable_cost": variable}
