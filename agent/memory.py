"""
EvolvixOS — Memory Store
Local SQLite database. No external services, no cloud, zero tokens.
Stores conversation history, task results, and learned knowledge.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


class MemoryStore:
    """Long-term memory using local SQLite. Fully offline."""

    def __init__(self, db_path: str = "./data/evolvix_memory.db"):
        self.db_path = db_path
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                fact TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS skills_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                action TEXT NOT NULL,
                result TEXT,
                success BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def add(self, content: str, memory_type: str = "general", metadata: dict = None):
        """Add a memory entry."""
        self.cursor.execute(
            "INSERT INTO memories (content, memory_type, metadata) VALUES (?, ?, ?)",
            (content, memory_type, json.dumps(metadata) if metadata else None)
        )
        self.conn.commit()

    def add_knowledge(self, topic: str, fact: str, source: str = None):
        """Add a learned fact."""
        self.cursor.execute(
            "INSERT INTO knowledge (topic, fact, source) VALUES (?, ?, ?)",
            (topic, fact, source)
        )
        self.conn.commit()

    def log_skill(self, skill_name: str, action: str, result: str, success: bool = True):
        """Log a skill execution."""
        self.cursor.execute(
            "INSERT INTO skills_log (skill_name, action, result, success) VALUES (?, ?, ?, ?)",
            (skill_name, action, result[:5000], success)
        )
        self.conn.commit()

    def search_memories(self, query: str, limit: int = 10) -> list:
        """Search memories by keyword."""
        self.cursor.execute(
            "SELECT id, content, memory_type, created_at FROM memories WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        return self.cursor.fetchall()

    def search_knowledge(self, topic: str) -> list:
        """Search knowledge by topic."""
        self.cursor.execute(
            "SELECT id, topic, fact, source, created_at FROM knowledge WHERE topic LIKE ? ORDER BY created_at DESC",
            (f"%{topic}%",)
        )
        return self.cursor.fetchall()

    def get_recent_memories(self, limit: int = 20) -> list:
        """Get recent memories."""
        self.cursor.execute(
            "SELECT id, content, memory_type, created_at FROM memories ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_skill_stats(self) -> dict:
        """Get statistics on skill usage."""
        self.cursor.execute(
            "SELECT skill_name, COUNT(*) as count, SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count FROM skills_log GROUP BY skill_name"
        )
        results = self.cursor.fetchall()
        return {
            row[0]: {"total": row[1], "successes": row[2]}
            for row in results
        }

    def close(self):
        self.conn.close()
