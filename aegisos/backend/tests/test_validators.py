"""Tests for Validator Management — Phase 37."""

import pytest
import time
from app.services.validators import (
    ValidatorService, get_validator_service, ValidatorStatus,
)


class TestRegistration:
    def test_register_validator(self):
        service = ValidatorService(max_validators=101)
        v = service.register_validator("0xnew", "Test Val", energy_source="solar", green_score=85)
        assert v.id.startswith("val-")
        assert v.status == "active"
        assert v.energy_source == "solar"

    def test_register_duplicate_address(self):
        service = ValidatorService(max_validators=101)
        v1 = service.register_validator("0xdupe", "Val 1")
        v2 = service.register_validator("0xdupe", "Val 2")
        assert v1.id == v2.id  # Returns existing

    def test_max_validators(self):
        service = ValidatorService(max_validators=30)
        for i in range(16):
            service.register_validator(f"0x{i:02d}", f"Val {i}")
        with pytest.raises(ValueError):
            service.register_validator("0xextra", "Extra")

    def test_default_validators(self):
        service = ValidatorService()
        assert len(service.list_validators()) == 14

    def test_get_validator(self):
        service = ValidatorService()
        v = service.register_validator("0xget", "Test")
        found = service.get_validator(v.id)
        assert found is not None
        assert found.name == "Test"

    def test_get_by_address(self):
        service = ValidatorService()
        v = service.register_validator("0xaddr", "ByAddr")
        found = service.get_validator_by_address("0xaddr")
        assert found is not None
        assert found.id == v.id


class TestValidatorOps:
    def test_pause_activate(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        assert service.pause_validator(v.id) is True
        assert service.get_validator(v.id).status == "paused"
        assert service.activate_validator(v.id) is True
        assert service.get_validator(v.id).status == "active"

    def test_slash(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        original_stake = v.total_stake
        assert service.slash_validator(v.id, "double sign") is True
        assert v.status == "slashed"
        assert v.total_stake < original_stake

    def test_remove(self):
        service = ValidatorService()
        v = service.register_validator("0xrm", "Remove")
        assert service.remove_validator(v.id) is True
        assert service.get_validator(v.id).status == "ejected"

    def test_list_by_status(self):
        service = ValidatorService()
        active = service.list_validators(status="active")
        assert all(v.status == "active" for v in active)

    def test_list_by_certified(self):
        service = ValidatorService()
        certified = service.list_validators(certified=True)
        assert all(v.certified for v in certified)

    def test_list_sorted(self):
        service = ValidatorService()
        by_stake = service.list_validators(sort_by="stake")
        stakes = [v.total_stake for v in by_stake]
        assert stakes == sorted(stakes, reverse=True)

    def test_list_sorted_green(self):
        service = ValidatorService()
        by_green = service.list_validators(sort_by="green")
        scores = [v.green_score for v in by_green]
        assert scores == sorted(scores, reverse=True)


class TestGreenScore:
    def test_update_green_score(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.update_green_score(v.id, 95, "geothermal", 200)
        assert v.green_score == 95
        assert v.energy_source == "geothermal"
        assert v.carbon_offset == 200

    def test_certify_high_score(self):
        service = ValidatorService()
        v = service.register_validator("0xcert", "Cert", green_score=70)
        assert service.certify_validator(v.id) is False  # Below 80
        service.update_green_score(v.id, 85)
        assert v.certified is True  # Auto-certified at >= 80

    def test_clamp_score(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.update_green_score(v.id, 150)
        assert v.green_score == 100
        service.update_green_score(v.id, -10)
        assert v.green_score == 0


class TestDelegation:
    def test_delegate(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        d = service.delegate("0xdel1", v.id, 10000)
        assert d.id.startswith("del-")
        assert d.amount == 10000

    def test_delegate_inactive_validator(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.pause_validator(v.id)
        assert service.delegate("0xdel", v.id, 100) is None

    def test_undelegate(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        d = service.delegate("0xdel1", v.id, 5000)
        assert service.undelegate(d.id) is True
        assert d.active is False

    def test_list_delegations(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.delegate("0xa", v.id, 100)
        service.delegate("0xb", v.id, 200)
        dels = service.list_delegations(validator_id=v.id)
        assert len(dels) >= 2

    def test_list_by_delegator(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.delegate("0xdelegator", v.id, 100)
        dels = service.list_delegations(delegator="0xdelegator")
        assert all(d.delegator == "0xdelegator" for d in dels)


class TestBlockProduction:
    def test_record_block_produced(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.record_block_production(v.id, True)
        assert v.blocks_produced == 1
        assert v.uptime_pct == 100.0

    def test_record_block_missed(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.record_block_production(v.id, True)
        service.record_block_production(v.id, False)
        assert v.blocks_missed == 1
        assert v.uptime_pct == 50.0

    def test_get_events(self):
        service = ValidatorService()
        v = service.list_validators()[0]
        service.record_block_production(v.id, True)
        events = service.get_validator_events(v.id)
        assert len(events) >= 1


class TestGrades:
    def test_grade_a(self):
        service = ValidatorService()
        v = service.list_validators(status="active", sort_by="green")[0]
        grade = service.get_validator_grade(v.id)
        assert grade in ("A", "B", "C", "D")

    def test_grade_nonexistent(self):
        service = ValidatorService()
        assert service.get_validator_grade("nonexistent") == "D"


class TestStats:
    def test_network_stats(self):
        service = ValidatorService()
        stats = service.get_network_stats()
        assert stats["total_validators"] == 14
        assert stats["active_validators"] == 14
        assert stats["max_validators"] == 101
        assert stats["total_stake"] > 0
        assert stats["avg_green_score"] > 0

    def test_dashboard(self):
        service = ValidatorService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "top_validators" in dash
        assert "greenest_validators" in dash
        assert len(dash["top_validators"]) <= 10


class TestMonitoring:
    def test_start_stop(self):
        service = ValidatorService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False

    def test_start_already_running(self):
        service = ValidatorService()
        service.start_monitoring(interval=10)
        service.start_monitoring(interval=10)
        assert service.is_monitoring() is True
        service.stop_monitoring()


class TestValidatorAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/validators/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/validators/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_validators"] >= 14

    def test_list(self, client, test_user):
        resp = client.get("/api/v1/validators", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 14

    def test_register(self, client, test_user):
        resp = client.post("/api/v1/validators/", json={
            "address": "0xapival", "name": "API Val", "energy_source": "solar",
            "green_score": 90, "carbon_offset": 150,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["name"] == "API Val"

    def test_delegate(self, client, test_user):
        vals = client.get("/api/v1/validators", headers=test_user["headers"]).json()
        vid = vals[0]["id"]
        resp = client.post("/api/v1/validators/delegate", json={
            "delegator": "0xtest", "validator_id": vid, "amount": 1000,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("del-")

    def test_grade(self, client, test_user):
        vals = client.get("/api/v1/validators", headers=test_user["headers"]).json()
        vid = vals[0]["id"]
        resp = client.get(f"/api/v1/validators/{vid}/grade", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["grade"] in ("A", "B", "C", "D")

    def test_singleton(self):
        assert get_validator_service() is get_validator_service()
