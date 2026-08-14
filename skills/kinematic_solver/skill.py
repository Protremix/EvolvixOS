#!/usr/bin/env python3
"""Kinematic SUVAT Solver - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        u = float(args.get("u", 0.0))
        a = float(args.get("a", 9.81))
        t = float(args.get("t", 2.0))
        v = u + a * t
        s = u * t + 0.5 * a * (t ** 2)
        return {"initial_velocity_u": u, "final_velocity_v": round(v, 2), "displacement_s": round(s, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
