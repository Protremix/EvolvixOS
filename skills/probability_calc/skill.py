#!/usr/bin/env python3
"""Probability Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        formula = args.get("formula", "combinations")
        n = args.get("n", 0)
        r = args.get("r", 0)
        formulas = {
            "combinations": math.comb(n, r) if n >= r >= 0 else 0,
            "permutations": math.perm(n, r) if n >= r >= 0 else 0,
            "factorial": math.factorial(n) if n >= 0 else 0,
            "binomial": math.comb(n, r) * (args.get("p", 0.5)**r) * ((1-args.get("p", 0.5))**(n-r)) if n >= r >= 0 else 0,
            "poisson": (args.get("lambda", 1)**n * math.exp(-args.get("lambda", 1))) / math.factorial(n) if n >= 0 else 0,
            "normal_cdf": 0.5 * (1 + math.erf((n - args.get("mean", 0)) / (args.get("std", 1) * math.sqrt(2)))) if args.get("std", 1) > 0 else 0,
            "bayes": (args.get("p_b_given_a", 0.5) * args.get("p_a", 0.5)) / args.get("p_b", 0.5) if args.get("p_b", 0) else 0,
        }
        result = formulas.get(formula)
        if result is None:
            return {"error": f"Unknown. Available: {list(formulas.keys())}"}
        return {"formula": formula, "result": result, "n": n, "r": r}
