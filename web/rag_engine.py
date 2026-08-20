"""EvolvixOS RAG Engine v2.0 — Retrieval-Augmented Generation"""
import sqlite3, json, os, time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="EvolvixOS RAG Engine", version="2.0")
DB_PATH = "/opt/evolvixos-platform-git/web/rag_engine.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        embedding BLOB,
        source TEXT,
        metadata TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source)')
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def root():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    count = c.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0]
    conn.close()
    return {"status": "online", "engine": "RAG v2.0", "documents": count}

@app.get("/health")
async def health():
    return {"status": "healthy", "engine": "RAG v2.0"}

@app.post("/ingest")
async def ingest(request: Request):
    body = await request.json()
    content = body.get("content", "")
    source = body.get("source", "unknown")
    metadata = json.dumps(body.get("metadata", {}))
    if not content:
        return JSONResponse({"error": "content required"}, status_code=400)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO embeddings (content, source, metadata) VALUES (?, ?, ?)', (content, source, metadata))
    conn.commit()
    doc_id = c.lastrowid
    conn.close()
    return {"status": "ingested", "id": doc_id}

@app.post("/search")
async def search(request: Request):
    body = await request.json()
    query = body.get("query", "").lower()
    limit = min(body.get("limit", 5), 50)
    if not query:
        return JSONResponse({"error": "query required"}, status_code=400)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    results = c.execute('SELECT id, content, source, metadata FROM embeddings WHERE LOWER(content) LIKE ? LIMIT ?', (f'%{query}%', limit)).fetchall()
    conn.close()
    return {"results": [{"id": r[0], "content": r[1], "source": r[2], "metadata": json.loads(r[3]) if r[3] else {}} for r in results]}

@app.get("/documents")
async def documents(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute('SELECT id, content, source, created_at FROM embeddings ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    conn.close()
    return {"documents": [{"id": r[0], "content": r[1][:200], "source": r[2], "created_at": r[3]} for r in rows]}

@app.delete("/documents/{doc_id}")
async def delete_doc(doc_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM embeddings WHERE id = ?', (doc_id,))
    conn.commit()
    deleted = c.rowcount
    conn.close()
    return {"status": "deleted", "id": doc_id, "affected": deleted}
