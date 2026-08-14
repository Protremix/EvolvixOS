#!/usr/bin/env python3
"""Discount Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        price = args.get("price", 100)
        discount = args.get("discount", 20)
        sale_price = price * (1 - discount / 100)
        savings = price - sale_price
        return {"original_price": price, "discount_percent": discount, "sale_price": round(sale_price, 2), "savings": round(savings, 2)}
