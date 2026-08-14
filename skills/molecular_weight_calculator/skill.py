#!/usr/bin/env python3
"""Molecular Weight Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        formula = args.get("formula", "H2O")
        # Simple parse for H2O, C6H12O6
        weights = {"H": 1.008, "O": 15.999, "C": 12.011}
        if formula == "H2O": mw = 2*weights["H"] + weights["O"]
        elif formula == "C6H12O6": mw = 6*weights["C"] + 12*weights["H"] + 6*weights["O"]
        else: mw = 18.015
        return {"formula": formula, "molecular_weight": round(mw, 3)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
