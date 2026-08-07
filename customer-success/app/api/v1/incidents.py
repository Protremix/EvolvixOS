"""Module 8: Incident Response."""
from fastapi import APIRouter, Request, Query
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter(prefix="/incidents", tags=["incident-response"])

class CreateIncident(BaseModel):
    title: str
    severity: str = "warning"
    source: str = "manual"
    description: str
    component: str = "general"
    auto_detect: bool = False

INCIDENT_TYPES = {
    "rpc_unavailable": {"severity": "critical", "component": "rpc", "team": "Infrastructure"},
    "node_offline": {"severity": "critical", "component": "blockchain", "team": "Blockchain"},
    "wallet_failure": {"severity": "high", "component": "wallet", "team": "Mobile"},
    "explorer_outage": {"severity": "high", "component": "explorer", "team": "Frontend"},
    "database_issue": {"severity": "critical", "component": "database", "team": "Infrastructure"},
    "api_degradation": {"severity": "warning", "component": "api", "team": "Backend"},
    "high_latency": {"severity": "warning", "component": "network", "team": "Infrastructure"},
    "disk_usage": {"severity": "warning", "component": "storage", "team": "Infrastructure"},
    "memory_usage": {"severity": "warning", "component": "system", "team": "Infrastructure"},
    "security_alert": {"severity": "critical", "component": "security", "team": "Security"},
}

@router.post("/")
async def create_incident(req: Request, incident: CreateIncident):
    """Create an incident."""
    record = database.insert("incidents", {
        "title": incident.title,
        "severity": incident.severity,
        "source": incident.source,
        "description": incident.description,
        "component": incident.component,
        "status": "active",
        "auto_detect": incident.auto_detect,
        "acknowledged": False,
        "resolved": False,
    })
    return record

@router.get("/")
async def list_incidents(req: Request, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 50):
    incidents = database.list_records("incidents",
        filter_fn=lambda r: (
            (not status or r.get("status") == status) and
            (not severity or r.get("severity") == severity)
        ),
        limit=limit)
    return {"incidents": incidents, "total": len(incidents)}

@router.get("/{incident_id}")
async def get_incident(incident_id: str, req: Request):
    incident = database.get("incidents", incident_id)
    if not incident:
        return {"error": "Incident not found"}
    events = database.list_records("incident_events",
        filter_fn=lambda r: r.get("incident_id") == incident_id)
    return {"incident": incident, "events": events}

@router.patch("/{incident_id}")
async def update_incident(incident_id: str, req: Request, status: Optional[str] = None,
    acknowledged: Optional[bool] = None, resolution: Optional[str] = None):
    data = {}
    if status: data["status"] = status
    if acknowledged is not None: data["acknowledged"] = acknowledged
    if resolution: data["resolution"] = resolution
    if status == "resolved":
        data["resolved"] = True
        data["resolved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    return database.update("incidents", incident_id, data) or {"error": "Not found"}

@router.get("/types/list")
async def list_incident_types():
    return {"types": list(INCIDENT_TYPES.keys()), "details": INCIDENT_TYPES}

@router.get("/stats")
async def incident_stats(req: Request):
    total = database.count("incidents")
    active = database.count("incidents", lambda r: r.get("status") == "active")
    resolved = database.count("incidents", lambda r: r.get("status") == "resolved")
    critical = database.count("incidents", lambda r: r.get("severity") == "critical" and r.get("status") == "active")
    return {"total": total, "active": active, "resolved": resolved, "critical_active": critical}

@router.post("/auto-detect")
async def auto_detect_incidents(req: Request):
    """Run automatic incident detection."""
    import httpx
    detected = []
    
    # Check blockchain RPC
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post("http://localhost:3200/blockchain/rpc", json={
                "jsonrpc": "2.0", "method": "system_health", "params": [], "id": 1
            })
            if resp.status_code != 200:
                detected.append({"type": "rpc_unavailable", "severity": "critical", "component": "rpc"})
    except Exception:
        detected.append({"type": "rpc_unavailable", "severity": "critical", "component": "rpc"})
    
    # Check API health
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:3200/api/v1/health")
            if resp.status_code != 200:
                detected.append({"type": "api_degradation", "severity": "warning", "component": "api"})
    except Exception:
        detected.append({"type": "api_degradation", "severity": "warning", "component": "api"})
    
    # Create incidents for detected issues
    for d in detected:
        incident_type = INCIDENT_TYPES.get(d["type"], {})
        database.insert("incidents", {
            "title": f"Auto-detected: {d['type']}",
            "severity": d["severity"],
            "source": "auto_detect",
            "description": f"Automatically detected {d['type']} on {d['component']}",
            "component": d["component"],
            "status": "active",
            "auto_detect": True,
            "acknowledged": False,
            "resolved": False,
        })
    
    return {"detected": detected, "incidents_created": len(detected)}
