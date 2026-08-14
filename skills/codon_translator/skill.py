#!/usr/bin/env python3
"""Codon Translator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        seq = args.get("dna", "ATGGCCTAG").upper()
        TABLE = {"ATG": "Met", "GCC": "Ala", "TAG": "Stop", "TTT": "Phe", "AAA": "Lys"}
        codons = [seq[i:i+3] for i in range(0, len(seq)-2, 3)]
        amino = [TABLE.get(c, "X") for c in codons]
        return {"codons": codons, "amino_acids": "-".join(amino)}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
