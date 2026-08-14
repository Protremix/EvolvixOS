#!/usr/bin/env python3
"""Ohm's Law Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        voltage = args.get("voltage", None)
        current = args.get("current", None)
        resistance = args.get("resistance", None)
        power = args.get("power", None)
        result = {}
        if voltage is None and current is not None and resistance is not None:
            voltage = current * resistance
        elif current is None and voltage is not None and resistance is not None:
            current = voltage / resistance
        elif resistance is None and voltage is not None and current is not None:
            resistance = voltage / current
        if voltage is not None and current is not None:
            power = voltage * current
        elif power is not None and voltage is not None:
            current = power / voltage
        elif power is not None and current is not None:
            voltage = power / current
        return {"voltage": voltage, "current": current, "resistance": resistance, "power": power}
