"""Tests for Tokenomics Dashboard — Phase 36."""

import pytest
from app.services.tokenomics import (
    TokenomicsService, get_tokenomics_service, AllocationType,
    VestingStatus, FlowType,
)


class TestSupply:
    def test_total_supply(self):
        service = TokenomicsService()
        assert service.get_total_supply() == 100_000_000_000

    def test_circulating_supply(self):
        service = TokenomicsService()
        supply = service.get_circulating_supply()
        assert supply["total_supply"] == 100_000_000_000
        assert supply["circulating"] > 0
        assert supply["circulating_pct"] > 0
        assert supply["locked"] > 0

    def test_investor_allocation(self):
        service = TokenomicsService()
        alloc = service.get_allocation(AllocationType.INVESTORS.value)
        assert alloc.total_amount == 12_000_000_000
        assert alloc.percentage == 12.0


class TestAllocations:
    def test_get_allocations(self):
        service = TokenomicsService()
        allocations = service.get_allocations()
        assert len(allocations) == 7
        assert sum(a.total_amount for a in allocations) == 100_000_000_000

    def test_get_allocation(self):
        service = TokenomicsService()
        alloc = service.get_allocation("validators")
        assert alloc is not None
        assert alloc.total_amount == 13_000_000_000

    def test_update_allocation(self):
        service = TokenomicsService()
        service.update_allocation("community", released=10_000_000_000)
        alloc = service.get_allocation("community")
        assert alloc.released == 10_000_000_000


class TestVesting:
    def test_create_vesting(self):
        service = TokenomicsService()
        s = service.create_vesting_schedule("0xinvestor", "investors", 1_000_000, 48, 12)
        assert s.id.startswith("vest-")
        assert s.total_amount == 1_000_000
        assert s.monthly_release > 0

    def test_get_vesting(self):
        service = TokenomicsService()
        s = service.create_vesting_schedule("0x1", "team", 500_000, 24, 6)
        found = service.get_vesting_schedule(s.id)
        assert found is not None
        assert found.beneficiary == "0x1"

    def test_list_vesting(self):
        service = TokenomicsService()
        service.create_vesting_schedule("0xa", "investors", 100_000, 12, 3)
        service.create_vesting_schedule("0xb", "team", 200_000, 24, 6)
        assert len(service.list_vesting_schedules()) >= 2

    def test_list_vesting_by_beneficiary(self):
        service = TokenomicsService()
        service.create_vesting_schedule("0xa", "investors", 100_000, 12, 3)
        service.create_vesting_schedule("0xb", "team", 200_000, 24, 6)
        a = service.list_vesting_schedules(beneficiary="0xa")
        assert all(s.beneficiary == "0xa" for s in a)

    def test_release_cliffed(self):
        service = TokenomicsService()
        s = service.create_vesting_schedule("0x1", "investors", 500_000, 48, 12)
        result = service.release_vested(s.id)
        assert result.status in ("cliffed", "vesting", "vested")

    def test_vesting_stats(self):
        service = TokenomicsService()
        service.create_vesting_schedule("0x1", "investors", 100_000, 12, 3)
        stats = service.get_vesting_stats()
        assert stats["total_schedules"] >= 1
        assert "total_vested" in stats


class TestFlows:
    def test_record_flow(self):
        service = TokenomicsService()
        flow = service.record_flow("transfer", "0xa", "0xb", 1000)
        assert flow.id.startswith("flow-")
        assert flow.amount == 1000

    def test_record_burn_flow(self):
        service = TokenomicsService()
        service.record_flow("burn", "0xa", "0x0", 5000)
        assert service.get_utility().burned == 5000

    def test_record_stake_flow(self):
        service = TokenomicsService()
        service.record_flow("stake", "0xa", "0xstaking", 20000)
        assert service.get_utility().staked_amount == 20000

    def test_list_flows(self):
        service = TokenomicsService()
        service.record_flow("transfer", "0xa", "0xb", 100)
        service.record_flow("mint", "0x0", "0xa", 200)
        assert len(service.list_flows()) >= 2

    def test_list_flows_by_type(self):
        service = TokenomicsService()
        service.record_flow("transfer", "0xa", "0xb", 100)
        service.record_flow("burn", "0xa", "0x0", 50)
        transfers = service.list_flows(flow_type="transfer")
        assert all(f.flow_type == "transfer" for f in transfers)

    def test_flow_stats(self):
        service = TokenomicsService()
        service.record_flow("transfer", "0xa", "0xb", 100)
        stats = service.get_flow_stats()
        assert stats["total_flows"] >= 1
        assert "total_volume" in stats


class TestUtility:
    def test_get_utility(self):
        service = TokenomicsService()
        util = service.get_utility()
        assert "staked_amount" in util.to_dict()
        assert "burned" in util.to_dict()

    def test_update_utility(self):
        service = TokenomicsService()
        service.update_utility(staked_amount=50000, governance_locked=10000)
        util = service.get_utility()
        assert util.staked_amount == 50000
        assert util.governance_locked == 10000


class TestDashboard:
    def test_dashboard(self):
        service = TokenomicsService()
        dash = service.get_dashboard()
        assert "supply" in dash
        assert "allocations" in dash
        assert "vesting" in dash
        assert "flows" in dash
        assert "utility" in dash
        assert dash["total_supply"] == 100_000_000_000

    def test_distribution_chart(self):
        service = TokenomicsService()
        chart = service.get_token_distribution_chart()
        assert "labels" in chart
        assert "values" in chart
        assert len(chart["labels"]) == 7

    def test_supply_progression(self):
        service = TokenomicsService()
        prog = service.get_supply_progression(12)
        assert "progression" in prog
        assert len(prog["progression"]) == 13  # 0-12 months


class TestTokenomicsAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/tokenomics/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_supply"] == 100_000_000_000

    def test_supply(self, client, test_user):
        resp = client.get("/api/v1/tokenomics/supply", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_supply"] == 100_000_000_000

    def test_allocations(self, client, test_user):
        resp = client.get("/api/v1/tokenomics/allocations", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    def test_create_vesting(self, client, test_user):
        resp = client.post("/api/v1/tokenomics/vesting", json={
            "beneficiary": "0xtest", "allocation_type": "investors",
            "total_amount": 100000, "vesting_months": 48, "cliff_months": 12,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("vest-")

    def test_record_flow(self, client, test_user):
        resp = client.post("/api/v1/tokenomics/flows", json={
            "flow_type": "transfer", "from_addr": "0xa", "to_addr": "0xb",
            "amount": 1000,
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("flow-")

    def test_distribution_chart(self, client, test_user):
        resp = client.get("/api/v1/tokenomics/distribution/chart", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["labels"]) == 7

    def test_supply_progression(self, client, test_user):
        resp = client.get("/api/v1/tokenomics/supply/progression?months=6", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()["progression"]) == 7

    def test_flow_types(self, client):
        resp = client.get("/api/v1/tokenomics/flow-types")
        assert resp.status_code == 200
        assert len(resp.json()) >= 8

    def test_singleton(self):
        assert get_tokenomics_service() is get_tokenomics_service()
