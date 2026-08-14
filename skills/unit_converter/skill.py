#!/usr/bin/env python3
"""Unit Converter - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        val = float(args.get("value", 1.0))
        from_u = args.get("from", "km").lower()
        to_u = args.get("to", "m").lower()
        rates = {"km_m": 1000, "m_km": 0.001, "mi_km": 1.60934, "km_mi": 0.621371, "kg_g": 1000, "g_kg": 0.001, "lb_kg": 0.453592}
        key = f"{from_u}_{to_u}"
        if from_u == "c" and to_u == "f": res = (val * 9/5) + 32
        elif from_u == "f" and to_u == "c": res = (val - 32) * 5/9
        elif key in rates: res = val * rates[key]
        else: res = val
        return {"value": val, "from": from_u, "to": to_u, "result": res}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
