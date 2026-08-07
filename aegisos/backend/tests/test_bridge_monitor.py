"""Tests for Bridge Monitoring — Phase 38."""

import pytest
import time
from app.services.bridge_monitor import (
    BridgeMonitorService, get_bridge_monitor_service,
    TransferStatus, BridgeStatus,
)


class TestTransfers:
    def test_create_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 1000)
        assert t.id.startswith("br-")
        assert t.status == "pending"
        assert t.amount == 1000

    def test_get_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("outbound", "verdis", "ethereum", "0x1", "0x2", 500)
        found = service.get_transfer(t.id)
        assert found is not None

    def test_list_transfers(self):
        service = BridgeMonitorService()
        service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.create_transfer("outbound", "verdis", "bsc", "0x3", "0x4", 200)
        assert len(service.list_transfers()) >= 2

    def test_list_by_status(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        pending = service.list_transfers(status="pending")
        assert all(t.status == "pending" for t in pending)

    def test_list_by_direction(self):
        service = BridgeMonitorService()
        service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.create_transfer("outbound", "verdis", "ethereum", "0x3", "0x4", 200)
        inbound = service.list_transfers(direction="inbound")
        assert all(t.direction == "inbound" for t in inbound)

    def test_list_by_chain(self):
        service = BridgeMonitorService()
        service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.create_transfer("inbound", "bsc", "verdis", "0x3", "0x4", 200)
        eth = service.list_transfers(source_chain="ethereum")
        assert all(t.source_chain == "ethereum" for t in eth)


class TestTransferLifecycle:
    def test_validate_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.validate_transfer(t.id, "relayer-1")
        assert t.validator_signatures == 1
        assert t.status == "pending"  # Need 3 signatures

    def test_full_validation(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.validate_transfer(t.id, "relayer-1")
        service.validate_transfer(t.id, "relayer-2")
        service.validate_transfer(t.id, "relayer-3")
        assert t.status == "validated"

    def test_execute_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        for i in range(1, 4):
            service.validate_transfer(t.id, f"relayer-{i}")
        result = service.execute_transfer(t.id, "0xtarget123", 500)
        assert result.status == "executed"
        assert result.tx_hash_target == "0xtarget123"

    def test_fail_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        result = service.fail_transfer(t.id, "Invalid proof")
        assert result.status == "failed"
        assert result.error == "Invalid proof"

    def test_refund_transfer(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.fail_transfer(t.id, "timeout")
        result = service.refund_transfer(t.id)
        assert result.status == "refunded"

    def test_execute_non_validated(self):
        service = BridgeMonitorService()
        t = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        result = service.execute_transfer(t.id)
        assert result is None  # Can't execute pending


class TestRelayers:
    def test_default_relayers(self):
        service = BridgeMonitorService()
        relayers = service.list_relayers()
        assert len(relayers) == 3

    def test_register_relayer(self):
        service = BridgeMonitorService()
        r = service.register_relayer("0xnew", "New Relayer")
        assert r.name == "New Relayer"
        assert r.active is True

    def test_remove_relayer(self):
        service = BridgeMonitorService()
        r = service.register_relayer("0xrm", "Remove Me")
        assert service.remove_relayer(r.id) is True
        assert service.get_relayer(r.id).active is False

    def test_activate_relayer(self):
        service = BridgeMonitorService()
        r = service.register_relayer("0xact", "Activate")
        service.remove_relayer(r.id)
        assert service.activate_relayer(r.id) is True
        assert service.get_relayer(r.id).active is True

    def test_update_relayer_stats(self):
        service = BridgeMonitorService()
        service.update_relayer_stats("relayer-1", latency_ms=75.0, success_rate=98.0)
        r = service.get_relayer("relayer-1")
        assert r.latency_ms == 75.0
        assert r.success_rate == 98.0


class TestAlerts:
    def test_default_alerts(self):
        service = BridgeMonitorService()
        alerts = service.list_alerts()
        assert len(alerts) >= 4

    def test_create_alert(self):
        service = BridgeMonitorService()
        a = service.create_alert("custom", "low", "Custom alert", threshold=50)
        assert a.id.startswith("alert-")
        assert a.triggered is False

    def test_large_transfer_alert(self):
        service = BridgeMonitorService()
        service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 2_000_000)
        triggered = service.list_alerts(triggered=True)
        assert any(a.alert_type == "large_transfer" for a in triggered)

    def test_failure_rate_alert(self):
        service = BridgeMonitorService()
        t1 = service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        service.fail_transfer(t1.id, "error")
        t2 = service.create_transfer("inbound", "ethereum", "verdis", "0x3", "0x4", 100)
        service.fail_transfer(t2.id, "error")
        triggered = service.list_alerts(triggered=True)
        assert any(a.alert_type == "high_failure_rate" for a in triggered)

    def test_relayer_down_alert(self):
        service = BridgeMonitorService()
        service.remove_relayer("relayer-1")
        service.remove_relayer("relayer-2")
        service.remove_relayer("relayer-3")
        triggered = service.list_alerts(triggered=True)
        assert any(a.alert_type == "relayer_down" for a in triggered)

    def test_reset_alert(self):
        service = BridgeMonitorService()
        a = service.create_alert("test", "low", "Test", threshold=10)
        a.triggered = True
        assert service.reset_alert(a.id) is True
        assert a.triggered is False

    def test_delete_alert(self):
        service = BridgeMonitorService()
        a = service.create_alert("temp", "low", "Temp", threshold=1)
        assert service.delete_alert(a.id) is True


class TestStats:
    def test_transfer_stats(self):
        service = BridgeMonitorService()
        service.create_transfer("inbound", "ethereum", "verdis", "0x1", "0x2", 100)
        stats = service.get_transfer_stats()
        assert stats["total_transfers"] >= 1
        assert "success_rate" in stats
        assert "failure_rate" in stats

    def test_bridge_health(self):
        service = BridgeMonitorService()
        health = service.get_bridge_health()
        assert health["status"] in ("operational", "degraded", "down", "maintenance")
        assert health["active_relayers"] >= 0
        assert "avg_latency_ms" in health

    def test_dashboard(self):
        service = BridgeMonitorService()
        dash = service.get_dashboard()
        assert "health" in dash
        assert "transfer_stats" in dash
        assert "relayers" in dash
        assert "alerts" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = BridgeMonitorService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestBridgeAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/bridge/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "health" in resp.json()

    def test_health(self, client, test_user):
        resp = client.get("/api/v1/bridge/health", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "status" in resp.json()

    def test_create_transfer(self, client, test_user):
        resp = client.post("/api/v1/bridge/transfers", json={
            "direction": "inbound", "source_chain": "ethereum",
            "target_chain": "verdis", "sender": "0x1", "recipient": "0x2",
            "amount": 1000,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("br-")

    def test_validate(self, client, test_user):
        create = client.post("/api/v1/bridge/transfers", json={
            "direction": "inbound", "source_chain": "ethereum",
            "target_chain": "verdis", "sender": "0x1", "recipient": "0x2",
            "amount": 500,
        }, headers=test_user["headers"])
        tid = create.json()["id"]
        resp = client.post(f"/api/v1/bridge/transfers/{tid}/validate", json={
            "relayer_id": "relayer-1",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["validator_signatures"] == 1

    def test_relayers(self, client, test_user):
        resp = client.get("/api/v1/bridge/relayers", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_singleton(self):
        assert get_bridge_monitor_service() is get_bridge_monitor_service()
