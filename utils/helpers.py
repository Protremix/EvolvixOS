# EvolvixOS — Utilities
# Shared helper functions used across skills and agent core.

import os
import json
import hashlib
import time
from pathlib import Path
from typing import Optional


def ensure_dir(path: str | Path) -> Path:
    """Ensure a directory exists, create if needed."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def hash_string(text: str) -> str:
    """Generate a short hash from a string."""
    return hashlib.md5(text.encode()).hexdigest()[:8]


def save_json(data, path: str | Path) -> None:
    """Save data as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: str | Path) -> Optional[dict]:
    """Load JSON from file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def timestamp() -> str:
    """Get current timestamp string."""
    return time.strftime("%Y%m%d_%H%M%S")


def truncate(text: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks for processing."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
