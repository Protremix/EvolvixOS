#!/usr/bin/env python3
"""Periodic Table Lookup - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        elem = args.get("element", "H").capitalize()
        ELEMENTS = {"H": {"name": "Hydrogen", "atomic_number": 1, "mass": 1.008}, "HE": {"name": "Helium", "atomic_number": 2, "mass": 4.0026}, "C": {"name": "Carbon", "atomic_number": 6, "mass": 12.011}, "O": {"name": "Oxygen", "atomic_number": 8, "mass": 15.999}}
        return ELEMENTS.get(elem, {"error": "Element not found"})

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
