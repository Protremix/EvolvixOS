"""Ticket management service."""
import time
import uuid
import difflib
from app.models import database

class TicketService:
    def create_ticket(self, conversation_id=None, title="", type="technical", priority="medium",
                      description="", user_id="anonymous", department="General", metadata=None) -> dict:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        return database.insert("tickets", {
            "id": ticket_id,
            "conversation_id": conversation_id,
            "title": title,
            "type": type,
            "priority": priority,
            "description": description,
            "user_id": user_id,
            "department": department,
            "status": "open",
            "metadata": metadata or {},
            "first_contact_resolution": False,
        })
    
    def get_ticket(self, ticket_id: str):
        return database.get("tickets", ticket_id)
    
    def update_ticket(self, ticket_id: str, data: dict):
        return database.update("tickets", ticket_id, data)
    
    def list_tickets(self, filters=None, limit=50, offset=0) -> list:
        def filter_fn(r):
            if not filters:
                return True
            return all(r.get(k) == v for k, v in filters.items())
        return database.list_records("tickets", filter_fn=filter_fn, limit=limit, offset=offset)
    
    def count_tickets(self, filters=None) -> int:
        def filter_fn(r):
            if not filters:
                return True
            return all(r.get(k) == v for k, v in filters.items())
        return database.count("tickets", filter_fn)
    
    def add_event(self, ticket_id: str, event_type: str, value: str) -> dict:
        return database.insert("ticket_events", {
            "ticket_id": ticket_id,
            "event_type": event_type,
            "value": value,
        })
    
    def get_ticket_events(self, ticket_id: str) -> list:
        return database.list_records("ticket_events",
            filter_fn=lambda r: r.get("ticket_id") == ticket_id, limit=100)
    
    def check_duplicate(self, title: str, description: str) -> dict:
        existing = database.list_records("tickets", limit=200)
        for t in existing:
            if t.get("status") in ["resolved", "closed"]:
                continue
            similarity = difflib.SequenceMatcher(None, title.lower(), t.get("title", "").lower()).ratio()
            if similarity > 0.7:
                return t
        return None
    
    def merge_tickets(self, source_id: str, target_id: str) -> dict:
        source = database.get("tickets", source_id)
        target = database.get("tickets", target_id)
        if not source or not target:
            return {"error": "Ticket not found"}
        
        # Merge metadata
        merged_meta = {**source.get("metadata", {}), **target.get("metadata", {})}
        database.update("tickets", target_id, {"metadata": merged_meta})
        database.update("tickets", source_id, {"status": "closed", "merged_into": target_id})
        
        return {"merged": True, "target": target_id, "source": source_id}
    
    def get_stats(self) -> dict:
        tickets = database.list_records("tickets", limit=1000)
        statuses = {}
        priorities = {}
        types = {}
        for t in tickets:
            s = t.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
            p = t.get("priority", "unknown")
            priorities[p] = priorities.get(p, 0) + 1
            tp = t.get("type", "unknown")
            types[tp] = types.get(tp, 0) + 1
        return {
            "total": len(tickets),
            "by_status": statuses,
            "by_priority": priorities,
            "by_type": types,
        }
