#!/usr/bin/env python3
"""NLP Processor - spaCy (MIT) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self._nlp = None

    def run(self, args: dict) -> dict:
        text = args.get("text", "")
        if not text:
            return {"error": "text required"}
        try:
            if self._nlp is None:
                import spacy
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except:
                    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
                    self._nlp = spacy.load("en_core_web_sm")
            doc = self._nlp(text)
            return {
                "entities": [{"text": e.text, "label": e.label_} for e in doc.ents],
                "sentences": len(list(doc.sents)),
                "keywords": [t.lemma_ for t in doc if not t.is_stop and not t.is_punct][:20],
            }
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "spacy"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
