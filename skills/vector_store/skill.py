#!/usr/bin/env python3
"""Vector Store - ChromaDB (Apache 2.0) - 100% Free"""
import json, sys, subprocess, os


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.pdir = self.config.get("persist_dir", os.path.expanduser("~/.evolvix/chromadb"))

    def run(self, args: dict) -> dict:
        action = args.get("action", "search")
        col = args.get("collection", "evolvix")
        try:
            import chromadb
            client = chromadb.PersistentClient(path=args.get("persist_dir", self.pdir))
            collection = client.get_or_create_collection(col)
            if action == "add":
                docs = args.get("documents", [])
                ids = args.get("ids", [f"doc_{i}" for i in range(len(docs))])
                collection.add(documents=docs, ids=ids)
                return {"added": len(docs), "total": collection.count()}
            elif action == "search":
                results = collection.query(query_texts=[args.get("query","")], n_results=args.get("n_results",5))
                return {"results": results}
            elif action == "count":
                return {"count": collection.count()}
            elif action == "clear":
                client.delete_collection(col)
                return {"deleted": col}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "chromadb"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
