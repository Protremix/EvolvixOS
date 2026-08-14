#!/usr/bin/env python3
"""Text Summarizer - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import re, collections
        text = args.get("text", "")
        ratio = float(args.get("ratio", 0.3))
        if not text:
            return {"error": "text is required"}
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if not sentences:
            return {"summary": "", "sentence_count": 0}
        words = re.findall(r'\w+', text.lower())
        stopwords = {"the", "a", "an", "is", "are", "and", "or", "in", "on", "at", "to", "for", "of", "with", "this", "that", "it"}
        filtered = [w for w in words if w not in stopwords and len(w) > 2]
        freq = collections.Counter(filtered)
        scored = []
        for s in sentences:
            score = sum(freq[w.lower()] for w in re.findall(r'\w+', s))
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        count = max(1, int(len(sentences) * ratio))
        summary = " ".join([s for _, s in scored[:count]])
        return {"summary": summary, "original_sentences": len(sentences), "summary_sentences": count}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
