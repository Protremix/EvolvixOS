#!/usr/bin/env python3
"""Embeddings Engine - sentence-transformers (Apache 2.0) - 100% Free"""
import json, sys, subprocess


class Skill:
    _model = None

    def __init__(self, config: dict = None):
        self.config = config or {}

    def _get_model(self):
        if Skill._model is None:
            from sentence_transformers import SentenceTransformer
            Skill._model = SentenceTransformer("all-MiniLM-L6-v2")
        return Skill._model

    def run(self, args: dict) -> dict:
        action = args.get("action", "embed")
        try:
            model = self._get_model()
            if action == "embed":
                texts = args.get("texts", [])
                if isinstance(texts, str): texts = [texts]
                embs = model.encode(texts)
                return {"embeddings": embs.tolist(), "dim": embs.shape[1]}
            elif action == "similarity":
                e = model.encode([args["text1"], args["text2"]])
                score = float(e[0] @ e[1] / (e[0].norm() * e[1].norm()))
                return {"similarity": score}
            elif action == "search":
                docs = args.get("documents", [])
                qe = model.encode([args["query"]])
                de = model.encode(docs)
                scores = (de @ qe.T).flatten().tolist()
                ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
                return {"results": [{"text": t, "score": float(s)} for t, s in ranked[:args.get("top_k",5)]]}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
