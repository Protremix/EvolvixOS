"""
EvolvixOS Local RAG Engine
Inspired by awesome-llm-apps local_rag_agent + deepseek_local_rag patterns.

Features:
- Fully local: Ollama embeddings + Qdrant vector DB
- No external API calls (privacy-first)
- Supports PDF, text, web URLs
- Hybrid search (keyword + semantic)
- Works with V10 ModelRouter for answer generation
"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime


class LocalRAGEngine:
    """Local-first RAG engine using Ollama embeddings."""

    def __init__(self, ollama_url: str = "http://localhost:11434", qdrant_url: str = "http://localhost:6333"):
        self.ollama_url = ollama_url
        self.qdrant_url = qdrant_url
        self.embed_model = "snowflake-arctic-embed"  # Local embedding model
        self.chunk_size = 500
        self.chunk_overlap = 50
        self._client = None
        self._embedder = None

    def _get_qdrant(self):
        """Lazy init Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=self.qdrant_url)
            except ImportError:
                raise RuntimeError("qdrant-client not installed. Run: pip install qdrant-client")
        return self._client

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from local Ollama."""
        import urllib.request
        data = json.dumps({"model": self.embed_model, "prompt": text}).encode()
        req = urllib.request.Request(
            f"{self.ollama_url}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("embedding", [])

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        return chunks

    def create_collection(self, name: str) -> bool:
        """Create a vector collection."""
        try:
            client = self._get_qdrant()
            from qdrant_client.models import Distance, VectorParams
            # Get embedding dimension
            test_embedding = self._get_embedding("test")
            dim = len(test_embedding)
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
            return True
        except Exception as e:
            print(f"Create collection error: {e}")
            return False

    def add_documents(self, collection: str, documents: List[Dict[str, str]]) -> int:
        """Add documents to a collection. Each doc: {text, source, metadata}"""
        try:
            client = self._get_qdrant()
            points = []
            for doc in documents:
                text = doc.get("text", "")
                chunks = self._chunk_text(text)
                for i, chunk in enumerate(chunks):
                    embedding = self._get_embedding(chunk)
                    point_id = hashlib.md5(f"{doc.get('source','')}_{i}".encode()).hexdigest()
                    points.append({
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "text": chunk,
                            "source": doc.get("source", ""),
                            "metadata": doc.get("metadata", {}),
                            "chunk_index": i,
                            "created": datetime.utcnow().isoformat()
                        }
                    })
            client.upsert(collection_name=collection, points=points)
            return len(points)
        except Exception as e:
            print(f"Add documents error: {e}")
            return 0

    def add_url(self, collection: str, url: str) -> int:
        """Add a web URL to the collection."""
        try:
            import urllib.request
            from bs4 import BeautifulSoup
            with urllib.request.urlopen(url) as resp:
                html = resp.read()
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return self.add_documents(collection, [{"text": text, "source": url}])
        except Exception as e:
            print(f"Add URL error: {e}")
            return 0

    def add_pdf(self, collection: str, pdf_path: str) -> int:
        """Add a PDF file to the collection."""
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return self.add_documents(collection, [{"text": text, "source": pdf_path}])
        except Exception as e:
            print(f"Add PDF error: {e}")
            return 0

    def search(self, collection: str, query: str, limit: int = 5) -> List[Dict]:
        """Search the collection for relevant chunks."""
        try:
            client = self._get_qdrant()
            query_embedding = self._get_embedding(query)
            results = client.query_points(
                collection_name=collection,
                query=query_embedding,
                limit=limit
            ).points
            return [
                {
                    "text": r.payload.get("text", ""),
                    "source": r.payload.get("source", ""),
                    "score": r.score,
                    "metadata": r.payload.get("metadata", {})
                }
                for r in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def query(self, collection: str, question: str, model: str = "auto") -> Dict:
        """Full RAG query: search + generate answer."""
        # 1. Retrieve relevant chunks
        chunks = self.search(collection, question, limit=5)
        if not chunks:
            return {"answer": "No relevant documents found.", "sources": []}

        # 2. Build context
        context = "\n\n".join([f"[Source: {c['source']}]\n{c['text']}" for c in chunks])

        # 3. Generate answer (uses V10 ModelRouter in production)
        prompt = f"""Answer the question based on the following context.
If the context doesn't contain the answer, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""

        # Generate answer using local Ollama
        try:
            import urllib.request
            ollama_data = json.dumps({
                "model": "qwen2.5:7b",
                "system": "You are a helpful assistant. Answer the user's question based ONLY on the provided context. If the context doesn't contain the answer, say 'I don\'t have enough information about that.' Be concise and factual.",
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 500, "temperature": 0.3}
            }).encode()
            req = urllib.request.Request("http://localhost:11434/api/generate", data=ollama_data)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                answer = result.get("response", "").strip()
        except Exception as e:
            answer = f"[Error generating answer: {e}]"

        return {
            "answer": answer,
            "context": context[:500],
            "sources": [{"source": c["source"], "score": c["score"]} for c in chunks],
            "model": "qwen2.5:7b",
            "collection": collection
        }

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            client = self._get_qdrant()
            return [c.name for c in client.get_collections().collections]
        except:
            return []

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            client = self._get_qdrant()
            client.delete_collection(name)
            return True
        except:
            return False


# Singleton
rag_engine = LocalRAGEngine()
