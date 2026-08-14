#!/usr/bin/env python3
"""Black-Scholes Option Pricer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math
        S = float(args.get("spot_price", 100.0))
        K = float(args.get("strike_price", 100.0))
        T = float(args.get("time_years", 1.0))
        r = float(args.get("risk_free_rate", 0.05))
        v = float(args.get("volatility", 0.2))
        d1 = (math.log(S / K) + (r + 0.5 * v**2) * T) / (v * math.sqrt(T))
        d2 = d1 - v * math.sqrt(T)
        N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
        call = S * N(d1) - K * math.exp(-r * T) * N(d2)
        put = K * math.exp(-r * T) * N(-d2) - S * N(-d1)
        return {"call_price": round(call, 2), "put_price": round(put, 2)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
