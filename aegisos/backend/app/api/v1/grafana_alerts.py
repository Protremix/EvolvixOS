"""Grafana Alert Webhook Receiver - Phase 81.

Receives alert notifications from Grafana and stores them as internal notifications.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import time
import json

from app.services.notifications import get_notification_service, NotificationType, NotificationSeverity

router = APIRouter(prefix="/notifications", tags=["grafana-alerts"])


class GrafanaAlert:
    """Parse Grafana webhook payload."""
    pass


@router.post("/webhook")
async def grafana_alert_webhook(request: Request):
    """Receive Grafana alert webhook and store as notification."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    alerts = payload.get("alerts", [])
    if not alerts and payload.get("title"):
        # Single alert format
        alerts = [payload]

    service = get_notification_service()
    results = []

    for alert in alerts:
        # Extract alert data
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        status = alert.get("status", "firing")
        severity = labels.get("severity", "warning")
        category = labels.get("category", "general")

        title = annotations.get("summary", alert.get("title", "Grafana Alert"))
        description = annotations.get("description", "")

        # Map severity
        notif_severity = NotificationSeverity.CRITICAL if severity == "critical" else NotificationSeverity.WARNING
        if status == "resolved":
            notif_severity = NotificationSeverity.INFO

        # Map category to notification type
        type_map = {
            "blockchain": NotificationType.BLOCK,
            "infrastructure": NotificationType.SYSTEM,
            "logs": NotificationType.SYSTEM,
            "web": NotificationType.SYSTEM,
            "backup": NotificationType.SYSTEM,
            "monitoring": NotificationType.SYSTEM,
        }
        notif_type = type_map.get(category, NotificationType.SYSTEM)

        # Create notification (broadcast to all users)
        message = f"[{severity.upper()}] {title}"
        if description:
            message += f"\n{description}"
        if status == "resolved":
            message = f"[RESOLVED] {title}"

        try:
            notif = service.create(
                user_address="system",
                type=notif_type,
                severity=notif_severity,
                title=f"[{severity.upper()}] {title}",
                message=message,
                action_url="https://evolvixos.com/grafana/alerting/list",
                action_label="View in Grafana",
                metadata={
                    "source": "grafana",
                    "category": category,
                    "status": status,
                    "labels": labels,
                    "annotations": annotations,
                    "fired_at": alert.get("startsAt", ""),
                    "resolved_at": alert.get("endsAt", "") if status == "resolved" else "",
                },
            )
            results.append({"alert": title, "status": status, "stored": True})
        except Exception as e:
            results.append({"alert": title, "status": status, "error": str(e)})

    return {"received": len(results), "results": results}


@router.post("/critical")
async def grafana_critical_webhook(request: Request):
    """Receive critical alert webhook."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    alerts = payload.get("alerts", [])
    service = get_notification_service()
    results = []

    for alert in alerts:
        annotations = alert.get("annotations", {})
        title = annotations.get("summary", "Critical Alert")
        description = annotations.get("description", "")

        try:
            notif = service.create(
                user_address="system",
                type=NotificationType.SYSTEM,
                severity=NotificationSeverity.CRITICAL,
                title=f"[CRITICAL] {title}",
                message=description or title,
                action_url="https://evolvixos.com/grafana/alerting/list",
                action_label="View Alert",
                metadata={"source": "grafana", "severity": "critical"},
            )
            results.append({"alert": title, "stored": True})
        except Exception as e:
            results.append({"alert": title, "error": str(e)})

    return {"received": len(results), "results": results}


@router.post("/warning")
async def grafana_warning_webhook(request: Request):
    """Receive warning alert webhook."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    alerts = payload.get("alerts", [])
    service = get_notification_service()
    results = []

    for alert in alerts:
        annotations = alert.get("annotations", {})
        title = annotations.get("summary", "Warning Alert")
        description = annotations.get("description", "")

        try:
            notif = service.create(
                user_address="system",
                type=NotificationType.SYSTEM,
                severity=NotificationSeverity.WARNING,
                title=f"[WARNING] {title}",
                message=description or title,
                action_url="https://evolvixos.com/grafana/alerting/list",
                action_label="View Alert",
                metadata={"source": "grafana", "severity": "warning"},
            )
            results.append({"alert": title, "stored": True})
        except Exception as e:
            results.append({"alert": title, "error": str(e)})

    return {"received": len(results), "results": results}
