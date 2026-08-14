#!/usr/bin/env python3
"""Fuel Cost Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        dist = float(args.get("distance_miles", 300.0))
        mpg = float(args.get("mpg", 25.0))
        price = float(args.get("price_per_gallon", 3.50))
        gallons = dist / mpg
        cost = gallons * price
        return {"gallons_needed": round(gallons, 2), "total_fuel_cost": round(cost, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
