#!/usr/bin/env python3
"""Profit Margin Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        revenue = float(args.get("revenue", 10000.0))
        cogs = float(args.get("cogs", 6000.0))
        expenses = float(args.get("operating_expenses", 2000.0))
        gross_profit = revenue - cogs
        net_profit = gross_profit - expenses
        return {
            "gross_margin_percent": round((gross_profit / revenue) * 100, 2) if revenue else 0,
            "net_margin_percent": round((net_profit / revenue) * 100, 2) if revenue else 0,
            "net_profit": net_profit
        }

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
