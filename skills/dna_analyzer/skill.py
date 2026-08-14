#!/usr/bin/env python3
"""DNA Analyzer — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        sequence = args.get("sequence", "").upper().replace(" ", "")
        if not sequence:
            return {"error": "sequence required"}
        complement_map = {"A": "T", "T": "A", "G": "C", "C": "G"}
        complement = "".join(complement_map.get(c, c) for c in sequence)
        gc_content = (sequence.count("G") + sequence.count("C")) / len(sequence) * 100 if sequence else 0
        codon_table = {"TTT": "Phe", "TTC": "Phe", "TTA": "Leu", "TTG": "Leu", "CTT": "Leu", "CTC": "Leu", "CTA": "Leu", "CTG": "Leu", "ATT": "Ile", "ATC": "Ile", "ATA": "Ile", "ATG": "Met", "GTT": "Val", "GTC": "Val", "GTA": "Val", "GTG": "Val", "TCT": "Ser", "TCC": "Ser", "TCA": "Ser", "TCG": "Ser", "CCT": "Pro", "CCC": "Pro", "CCA": "Pro", "CCG": "Pro", "ACT": "Thr", "ACC": "Thr", "ACA": "Thr", "ACG": "Thr", "GCT": "Ala", "GCC": "Ala", "GCA": "Ala", "GCG": "Ala", "TAT": "Tyr", "TAC": "Tyr", "TAA": "Stop", "TAG": "Stop", "TGA": "Stop", "CAT": "His", "CAC": "His", "CAA": "Gln", "CAG": "Gln", "AAT": "Asn", "AAC": "Asn", "AAA": "Lys", "AAG": "Lys", "GAT": "Asp", "GAC": "Asp", "GAA": "Glu", "GAG": "Glu", "TGT": "Cys", "TGC": "Cys", "TGA": "Stop", "TGG": "Trp", "CGT": "Arg", "CGC": "Arg", "CGA": "Arg", "CGG": "Arg", "AGT": "Ser", "AGC": "Ser", "AGA": "Arg", "AGG": "Arg", "GGT": "Gly", "GGC": "Gly", "GGA": "Gly", "GGG": "Gly"}
        codons = [sequence[i:i+3] for i in range(0, len(sequence)-2, 3)]
        protein = "-".join(codon_table.get(c, "???") for c in codons)
        return {
            "length": len(sequence),
            "complement": complement,
            "reverse_complement": complement[::-1],
            "gc_content": round(gc_content, 2),
            "a_count": sequence.count("A"),
            "t_count": sequence.count("T"),
            "g_count": sequence.count("G"),
            "c_count": sequence.count("C"),
            "protein": protein,
            "codon_count": len(codons),
        }
