#!/usr/bin/env python3
"""TF-IDF Calculator - Free & Local EvolvixOS Skill."""
import json, sys, os, math, re

class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
    def run(self, args: dict) -> dict:
        import math, collections
        docs = args.get("documents", ["the quick brown fox", "jumped over the lazy dog"])
        N = len(docs)
        doc_words = [d.lower().split() for d in docs]
        tf_list = [collections.Counter(w) for w in doc_words]
        df = collections.Counter()
        for words in doc_words: df.update(set(words))
        tfidf = []
        for i, tf in enumerate(tf_list):
            doc_scores = {}
            for w, count in tf.items():
                idf = math.log((N + 1) / (df[w] + 1)) + 1
                doc_scores[w] = round((count / len(doc_words[i])) * idf, 4)
            tfidf.append(doc_scores)
        return {"tfidf_matrices": tfidf}

if __name__ == '__main__':
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
