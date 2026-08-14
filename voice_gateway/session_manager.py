"""
Session Manager for EvolvixOS Voice Gateway.

Manages active voice conversation sessions, maintaining conversation history per session_id,
supporting thread-safe in-memory caching, optional SQLite persistence, and auto-expiration of inactive sessions.
"""

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class VoiceSessionManager:
    """Thread-safe voice conversation session manager."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        timeout_minutes: int = 30,
        max_messages: int = 50,
    ):
        """
        Initialize the session manager.

        :param db_path: Optional file path to SQLite database for persistent session storage.
        :param timeout_minutes: Inactivity duration in minutes before a session expires.
        :param max_messages: Maximum number of conversation messages retained per session.
        """
        self.db_path = db_path
        self.timeout_seconds = timeout_minutes * 60
        self.max_messages = max_messages
        self._lock = threading.Lock()

        # In-memory session cache structure:
        # session_id -> {
        #   "session_id": str,
        #   "created_at": float,
        #   "last_active": float,
        #   "metadata": dict,
        #   "history": list[dict]
        # }
        self._sessions: Dict[str, Dict[str, Any]] = {}

        if self.db_path:
            self._init_sqlite()
            self._load_from_sqlite()

    def _init_sqlite(self) -> None:
        """Initialize SQLite database tables for session persistence if configured."""
        if not self.db_path:
            return
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS voice_sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at REAL,
                        last_active REAL,
                        metadata TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS voice_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        role TEXT,
                        content TEXT,
                        timestamp REAL,
                        FOREIGN KEY(session_id) REFERENCES voice_sessions(session_id) ON DELETE CASCADE
                    )
                    """
                )
                conn.commit()
        except Exception:
            pass

    def _load_from_sqlite(self) -> None:
        """Load active, non-expired sessions from SQLite storage into memory."""
        if not self.db_path:
            return
        now = time.time()
        cutoff = now - self.timeout_seconds

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Select active sessions
                cursor.execute(
                    "SELECT session_id, created_at, last_active, metadata FROM voice_sessions WHERE last_active >= ?",
                    (cutoff,),
                )
                rows = cursor.fetchall()
                for row in rows:
                    sid = row["session_id"]
                    try:
                        meta = json.loads(row["metadata"]) if row["metadata"] else {}
                    except json.JSONDecodeError:
                        meta = {}

                    cursor.execute(
                        "SELECT role, content, timestamp FROM voice_messages WHERE session_id = ? ORDER BY id ASC",
                        (sid,),
                    )
                    msg_rows = cursor.fetchall()
                    history = [
                        {
                            "role": r["role"],
                            "content": r["content"],
                            "timestamp": r["timestamp"],
                        }
                        for r in msg_rows
                    ]

                    self._sessions[sid] = {
                        "session_id": sid,
                        "created_at": row["created_at"],
                        "last_active": row["last_active"],
                        "metadata": meta,
                        "history": history,
                    }
        except Exception:
            pass

    def _sync_session_to_sqlite(self, session_id: str) -> None:
        """Synchronize a session and its message history to SQLite."""
        if not self.db_path or session_id not in self._sessions:
            return
        sess = self._sessions[session_id]
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO voice_sessions (session_id, created_at, last_active, metadata)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        last_active=excluded.last_active,
                        metadata=excluded.metadata
                    """,
                    (
                        sess["session_id"],
                        sess["created_at"],
                        sess["last_active"],
                        json.dumps(sess["metadata"]),
                    ),
                )

                # Overwrite messages for session to keep in sync
                cursor.execute("DELETE FROM voice_messages WHERE session_id = ?", (session_id,))
                for msg in sess["history"]:
                    cursor.execute(
                        "INSERT INTO voice_messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                        (session_id, msg["role"], msg["content"], msg["timestamp"]),
                    )
                conn.commit()
        except Exception:
            pass

    def _delete_session_from_sqlite(self, session_id: str) -> None:
        """Remove session record and associated messages from SQLite."""
        if not self.db_path:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM voice_messages WHERE session_id = ?", (session_id,))
                cursor.execute("DELETE FROM voice_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
        except Exception:
            pass

    def cleanup_expired(self) -> int:
        """
        Purge sessions that have exceeded the inactivity timeout.

        :return: Count of purged expired sessions.
        """
        with self._lock:
            now = time.time()
            expired_ids = [
                sid
                for sid, sess in self._sessions.items()
                if (now - sess["last_active"]) > self.timeout_seconds
            ]
            for sid in expired_ids:
                del self._sessions[sid]
                self._delete_session_from_sqlite(sid)
            return len(expired_ids)

    def create_session(
        self, session_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session or refresh an existing session.

        :param session_id: Optional custom session identifier. Generated if not provided.
        :param metadata: Optional dictionary of metadata associated with the session.
        :return: The session_id.
        """
        with self._lock:
            now = time.time()
            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:12]}"

            if session_id in self._sessions:
                sess = self._sessions[session_id]
                sess["last_active"] = now
                if metadata:
                    sess["metadata"].update(metadata)
            else:
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "created_at": now,
                    "last_active": now,
                    "metadata": metadata or {},
                    "history": [],
                }

            self._sync_session_to_sqlite(session_id)
            return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session dictionary if active and non-expired. Updates last_active.

        :param session_id: The session ID to look up.
        :return: Session dict or None if not found or expired.
        """
        with self._lock:
            now = time.time()
            if session_id not in self._sessions:
                return None

            sess = self._sessions[session_id]
            if (now - sess["last_active"]) > self.timeout_seconds:
                del self._sessions[session_id]
                self._delete_session_from_sqlite(session_id)
                return None

            sess["last_active"] = now
            return dict(sess)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        """
        Append a conversation message (user/assistant) to a session.

        Prunes messages if exceeding max_messages. Creates session if non-existent.

        :param session_id: Target session ID.
        :param role: Message sender role ('user', 'assistant', 'system').
        :param content: Text content of the message.
        """
        with self._lock:
            now = time.time()
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "created_at": now,
                    "last_active": now,
                    "metadata": {},
                    "history": [],
                }

            sess = self._sessions[session_id]
            sess["last_active"] = now
            sess["history"].append({
                "role": role,
                "content": content,
                "timestamp": now,
            })

            # Trim history to max_messages limit
            if len(sess["history"]) > self.max_messages:
                sess["history"] = sess["history"][-self.max_messages:]

            self._sync_session_to_sqlite(session_id)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get message history for a given session.

        :param session_id: Target session ID.
        :return: List of message dictionaries.
        """
        sess = self.get_session(session_id)
        if not sess:
            return []
        return sess.get("history", [])

    def clear_session(self, session_id: str) -> bool:
        """
        Clear/delete a voice session.

        :param session_id: Session ID to clear.
        :return: True if session was found and removed, False otherwise.
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                self._delete_session_from_sqlite(session_id)
                return True
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active, non-expired sessions.

        :return: List of session overview dictionaries.
        """
        with self._lock:
            now = time.time()
            active_sessions = []
            expired_ids = []

            for sid, sess in self._sessions.items():
                if (now - sess["last_active"]) > self.timeout_seconds:
                    expired_ids.append(sid)
                else:
                    active_sessions.append({
                        "session_id": sid,
                        "created_at": sess["created_at"],
                        "last_active": sess["last_active"],
                        "message_count": len(sess["history"]),
                        "metadata": sess.get("metadata", {}),
                    })

            for sid in expired_ids:
                del self._sessions[sid]
                self._delete_session_from_sqlite(sid)

            return active_sessions
