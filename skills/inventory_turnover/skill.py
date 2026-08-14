#!/usr/bin/env python3
"""Inventory Turnover Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        cogs = float(args.get("cogs", 500000.0))
        avg_inv = float(args.get("avg_inventory", 100000.0))
        turnover = cogs / avg_inv if avg_inv else 0
        dsi = 365.0 / turnover if turnover else 0
        return {"inventory_turnover_ratio": round(turnover, 2), "days_sales_of_inventory": round(dsi, 1)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
