#!/usr/bin/env python3
"""Matrix Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        m1 = args.get("matrix1", [[1, 2], [3, 4]])
        m2 = args.get("matrix2", [[5, 6], [7, 8]])
        # Addition
        add = [[m1[i][j] + m2[i][j] for j in range(len(m1[0]))] for i in range(len(m1))]
        return {"addition": add}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
