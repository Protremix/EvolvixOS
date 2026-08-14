#!/usr/bin/env python3
"""TF-IDF Calculator — 100% Free, 100% Local"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        import math
        from collections import Counter
        import re
        documents = args.get("documents", [])
        if not documents:
            return {"error": "documents required"}
        doc_words = [re.findall(r'\b\w+\b', doc.lower()) for doc in documents]
        doc_freq = Counter()
        for words in doc_words:
            for w in set(words):
                doc_freq[w] += 1
        n_docs = len(documents)
        idf = {w: math.log(n_docs / (1 + df)) for w, df in doc_freq.items()}
        results = []
        for i, words in enumerate(doc_words):
            tf = Counter(words)
            total = len(words)
            scores = {w: (tf[w] / total) * idf.get(w, 0) for w in tf}
            top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
            results.append({"doc": i, "top_terms": [{"term": t, "score": round(s, 4)} for t, s in top]})
        return {"results": results, "documents": n_docs, "vocabulary": len(doc_freq)}
