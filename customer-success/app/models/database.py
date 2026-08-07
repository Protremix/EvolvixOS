"""Database models for Customer Success Platform."""
import os
import time
import json
from typing import Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading
import uuid

# In-memory storage (will be replaced with PostgreSQL in production)
_store = {}
_lock = threading.Lock()

def init_db():
    """Initialize database tables."""
    tables = [
        "conversations", "messages", "tickets", "ticket_events",
        "knowledge_entries", "knowledge_sources",
        "email_threads", "email_messages",
        "incidents", "incident_events",
        "escalations", "escalation_transfers",
        "merchant_tickets", "developer_tickets",
        "blockchain_diagnostics", "node_health",
        "learning_entries", "solutions",
        "satisfaction_ratings", "audit_logs",
        "users", "departments",
    ]
    with _lock:
        for t in tables:
            if t not in _store:
                _store[t] = {}

def get_table(name: str) -> dict:
    with _lock:
        return _store.get(name, {})

def insert(name: str, record: dict) -> dict:
    with _lock:
        if name not in _store:
            _store[name] = {}
        record_id = record.get("id", str(uuid.uuid4()))
        record["id"] = record_id
        record["created_at"] = record.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
        record["updated_at"] = record.get("updated_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
        _store[name][record_id] = record
        return record

def update(name: str, record_id: str, data: dict) -> Optional[dict]:
    with _lock:
        if name in _store and record_id in _store[name]:
            _store[name][record_id].update(data)
            _store[name][record_id]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            return _store[name][record_id]
    return None

def get(name: str, record_id: str) -> Optional[dict]:
    with _lock:
        return _store.get(name, {}).get(record_id)

def list_records(name: str, filter_fn=None, limit: int = 100, offset: int = 0) -> list:
    with _lock:
        records = list(_store.get(name, {}).values())
    if filter_fn:
        records = [r for r in records if filter_fn(r)]
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return records[offset:offset + limit]

def delete(name: str, record_id: str) -> bool:
    with _lock:
        if name in _store and record_id in _store[name]:
            del _store[name][record_id]
            return True
    return False

def count(name: str, filter_fn=None) -> int:
    with _lock:
        records = list(_store.get(name, {}).values())
    if filter_fn:
        return sum(1 for r in records if filter_fn(r))
    return len(records)
