"""
OpenViking Bridge — Integrates OpenViking context database with EvolvixOS platform.

OpenViking runs as a separate service (port 8200). This bridge communicates
via HTTP only — no code linking, keeping the MIT license clean.

Key capabilities:
- Semantic search across indexed resources (code, docs, repos)
- Session-based memory extraction (auto-learns from conversations)
- Skill storage and retrieval
- Content write/read for explicit knowledge storage
- Filesystem browsing of the viking:// context tree
"""

import json
import urllib.request
import urllib.error
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger("openviking_bridge")

OPENVIKING_URL = "http://127.0.0.1:8200"
DEFAULT_ACCOUNT = "default"
DEFAULT_USER = "default"


def _request(method: str, path: str, data: Optional[dict] = None, timeout: int = 60) -> dict:
    """Make an HTTP request to the OpenViking server."""
    url = f"{OPENVIKING_URL}{path}"
    headers = {
        "Content-Type": "application/json",
        "X-OpenViking-Account": DEFAULT_ACCOUNT,
        "X-OpenViking-User": DEFAULT_USER,
    }
    payload = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read().decode()
        return json.loads(body) if body else {"status": "ok"}
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        logger.error(f"OpenViking HTTP {e.code}: {body[:500]}")
        return {"error": True, "status": e.code, "message": body[:500]}
    except Exception as e:
        logger.error(f"OpenViking request failed: {e}")
        return {"error": True, "message": str(e)}


def health_check() -> dict:
    """Check if OpenViking is healthy."""
    try:
        req = urllib.request.Request(f"{OPENVIKING_URL}/health")
        resp = urllib.request.urlopen(req, timeout=5)
        return json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Resource Management ──

def add_resource(source: str, wait: bool = False) -> dict:
    """Add a resource (repo, URL, file) to the context store."""
    return _request("POST", "/api/v1/resources", {
        "source": source,
        "wait": wait,
    }, timeout=600)


def list_resources() -> dict:
    """List all resources in the filesystem."""
    return _request("GET", "/api/v1/fs/ls?uri=viking://resources")


# ── Semantic Search ──

def search(query: str, limit: int = 5, mode: str = "thinking") -> dict:
    """Semantic search across all context (code, docs, memories)."""
    return _request("POST", "/api/v1/search/search", {
        "query": query,
        "limit": limit,
        "mode": mode,
    })


def recall(query: str, limit: int = 5) -> dict:
    """Recall relevant context — optimized for agent context injection."""
    return _request("POST", "/api/v1/search/recall", {
        "query": query,
    })


def grep(pattern: str, path: str = "viking://") -> dict:
    """Grep within indexed content."""
    return _request("POST", "/api/v1/search/grep", {
        "pattern": pattern,
        "path": path,
    })


# ── Content Management (explicit knowledge storage) ──

def write_content(uri: str, content: str, tags: Optional[List[str]] = None) -> dict:
    """Write content to a viking:// URI — for explicit knowledge storage."""
    return _request("POST", "/api/v1/content/write", {
        "uri": uri,
        "content": content,
    })


def read_content(uri: str) -> dict:
    """Read content from a viking:// URI."""
    return _request("GET", f"/api/v1/content/read?uri={uri}")


def get_overview(uri: str) -> dict:
    """Get L1 overview of a resource (structured summary)."""
    return _request("GET", f"/api/v1/content/overview?uri={uri}")


def get_abstract(uri: str) -> dict:
    """Get L0 abstract of a resource (one-sentence summary)."""
    return _request("GET", f"/api/v1/content/abstract?uri={uri}")


# ── Session Management (memory extraction) ──

def create_session(title: str = "") -> dict:
    """Create a new session for memory tracking."""
    return _request("POST", "/api/v1/sessions", {"title": title})


def list_sessions() -> dict:
    """List all sessions."""
    return _request("GET", "/api/v1/sessions")


def add_message(session_id: str, role: str, content: str) -> dict:
    """Add a message to a session."""
    return _request("POST", f"/api/v1/sessions/{session_id}/messages", {
        "role": role,
        "content": content,
    })


def add_messages_batch(session_id: str, messages: List[dict]) -> dict:
    """Add multiple messages to a session in one call."""
    return _request("POST", f"/api/v1/sessions/{session_id}/messages/batch", {
        "messages": messages,
    })


def commit_session(session_id: str) -> dict:
    """Commit a session — triggers async memory extraction."""
    return _request("POST", f"/api/v1/sessions/{session_id}/commit", {})


def get_session_context(session_id: str) -> dict:
    """Get the context/memories extracted from a session."""
    return _request("GET", f"/api/v1/sessions/{session_id}/context")


def extract_session(session_id: str) -> dict:
    """Manually trigger memory extraction for a session."""
    return _request("POST", f"/api/v1/sessions/{session_id}/extract", {})


def get_memory_stats() -> dict:
    """Get statistics about stored memories."""
    return _request("GET", "/api/v1/stats/memories")


# ── Filesystem Operations ──

def list_context(path: str = "viking://") -> dict:
    """List context at a given viking:// path."""
    return _request("GET", f"/api/v1/fs/ls?uri={path}")


def tree_context(path: str = "viking://", depth: int = 2) -> dict:
    """Show tree of context at a given path."""
    return _request("GET", f"/api/v1/fs/tree?uri={path}&depth={depth}")


def stat_context(path: str) -> dict:
    """Get attributes/stats of a context path."""
    return _request("GET", f"/api/v1/fs/stat?uri={path}")


def make_dir(path: str) -> dict:
    """Create a directory in the viking:// filesystem."""
    return _request("POST", "/api/v1/fs/mkdir", {"path": path})


# ── Skill Management ──

def save_skill(name: str, description: str, code: str, tags: Optional[List[str]] = None) -> dict:
    """Save a reusable skill to the context store."""
    return _request("POST", "/api/v1/skills", {
        "name": name,
        "description": description,
        "code": code,
        "tags": tags or [],
    })


def list_skills() -> dict:
    """List all stored skills."""
    return _request("GET", "/api/v1/skills")


def find_skills(query: str, limit: int = 5) -> dict:
    """Semantic search for skills."""
    return _request("POST", "/api/v1/skills/find", {
        "query": query,
        "limit": limit,
    })


def get_skill(name: str) -> dict:
    """Get a specific skill by name."""
    return _request("GET", f"/api/v1/skills/{name}")


# ── Agent Evolution (self-improvement) ──

def get_evolution_outcomes() -> dict:
    """Get agent evolution experience outcomes."""
    return _request("GET", "/api/v1/agent-evolution/experiences/outcomes")


def get_evolution_trajectories() -> dict:
    """Get agent evolution experience trajectories."""
    return _request("GET", "/api/v1/agent-evolution/experiences/trajectories")


# ── High-level convenience API ──

def store_knowledge(key: str, content: str, category: str = "knowledge") -> dict:
    """Store explicit knowledge at a predictable URI.
    
    Creates viking://resources/evolvixos/{category}/{key}
    """
    uri = f"viking://resources/evolvixos/{category}/{key}"
    # Ensure parent dirs exist
    make_dir(f"viking://resources/evolvixos/{category}")
    return write_content(uri, content, tags=[category])


def recall_for_agent(query: str, limit: int = 5) -> dict:
    """Recall relevant context for an agent task — combines search + recall."""
    results = recall(query, limit=limit)
    if results.get("error"):
        # Fallback to regular search
        results = search(query, limit=limit)
    return results
