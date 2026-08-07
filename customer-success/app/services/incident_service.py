"""Incident response service."""
import time
from app.models import database

class IncidentService:
    def create_incident(self, title, severity, source, description, component):
        return database.insert("incidents", {
            "title": title,
            "severity": severity,
            "source": source,
            "description": description,
            "component": component,
            "status": "active",
            "acknowledged": False,
            "resolved": False,
        })
    
    def get_incident(self, incident_id):
        return database.get("incidents", incident_id)
    
    def update_incident(self, incident_id, data):
        return database.update("incidents", incident_id, data)
    
    def list_incidents(self, filters=None, limit=50):
        return database.list_records("incidents",
            filter_fn=lambda r: (not filters or all(r.get(k) == v for k, v in filters.items())),
            limit=limit)
    
    def add_event(self, incident_id, event_type, value):
        return database.insert("incident_events", {
            "incident_id": incident_id,
            "event_type": event_type,
            "value": value,
        })
