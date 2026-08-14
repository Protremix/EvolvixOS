#!/usr/bin/env python3
"""Fuel Cost Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        distance = args.get("distance", 100)
        mpg = args.get("mpg", 30)
        price = args.get("price", 3.50)
        gallons = distance / mpg
        cost = gallons * price
        return {"distance": distance, "fuel_needed": round(gallons, 2), "cost": round(cost, 2), "mpg": mpg, "price_per_gallon": price}
