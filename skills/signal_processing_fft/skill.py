#!/usr/bin/env python3
"""Discrete Fourier Transform (DFT) - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import cmath, math
        signal = args.get("signal", [1, 0, -1, 0])
        N = len(signal)
        X = []
        for k in range(N):
            s = sum(signal[n] * cmath.exp(-2j * math.pi * k * n / N) for n in range(N))
            X.append(round(abs(s), 4))
        return {"magnitudes": X}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
