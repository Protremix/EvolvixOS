#!/usr/bin/env python3
"""Math Solver - SymPy (BSD) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "solve")
        try:
            from sympy import symbols, solve, simplify, diff, integrate, sympify
            x = symbols("x")
            if action == "solve":
                eq = sympify(args["equation"])
                return {"solutions": [str(s) for s in solve(eq, x)]}
            elif action == "derive":
                expr = sympify(args["expression"])
                return {"derivative": str(simplify(diff(expr, x)))}
            elif action == "integrate":
                expr = sympify(args["expression"])
                return {"integral": str(integrate(expr, x))}
            elif action == "simplify":
                return {"simplified": str(simplify(sympify(args["expression"])))}
            elif action == "evaluate":
                return {"result": str(sympify(args["expression"]).evalf())}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sympy"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
