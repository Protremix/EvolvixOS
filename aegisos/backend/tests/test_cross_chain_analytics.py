"""Tests for Cross-Chain Analytics — Phase 42."""

import pytest
import time
from app.services.cross_chain_analytics import (
    CrossChainAnalyticsService, get_cross_chain_analytics_service, ChainType,
)


class TestTransfers:
    def test_record_transfer(self):
        service = CrossChainAnalyticsService()
        t = service.record_transfer("ethereum", "verdis", "VRS", 1000, "0x1", "0x2")
        assert t.id.startswith("xfer-")
        assert t.source_chain == "ethereum"
        assert t.status == "confirmed"

    def test_get_transfer(self):
        service = CrossChainAnalyticsService()
        t = service.record_transfer("ethereum", "verdis", "VRS", 1000, "0x1", "0x2")
        found = service.get_transfer(t.id)
        assert found is not None

    def test_list_transfers(self):
        service = CrossChainAnalyticsService()
        all_t = service.list_transfers(limit=50)
        assert len(all_t) > 0

    def test_filter_by_source(self):
        service = CrossChainAnalyticsService()
        eth = service.list_transfers(source_chain="ethereum")
        assert all(t.source_chain == "ethereum" for t in eth)

    def test_filter_by_target(self):
        service = CrossChainAnalyticsService()
        verdis = service.list_transfers(target_chain="verdis")
        assert all(t.target_chain == "verdis" for t in verdis)

    def test_filter_by_token(self):
        service = CrossChainAnalyticsService()
        vrs = service.list_transfers(token="VRS")
        assert all(t.token == "VRS" for t in vrs)

    def test_filter_by_status(self):
        service = CrossChainAnalyticsService()
        confirmed = service.list_transfers(status="confirmed")
        assert all(t.status == "confirmed" for t in confirmed)

    def test_filter_by_amount(self):
        service = CrossChainAnalyticsService()
        big = service.list_transfers(min_amount=10000)
        assert all(t.amount >= 10000 for t in big)

    def test_sort_by_amount(self):
        service = CrossChainAnalyticsService()
        by_amount = service.list_transfers(sort_by="amount", limit=10)
        amounts = [t.amount for t in by_amount]
        assert amounts == sorted(amounts, reverse=True)


class TestChainMetrics:
    def test_get_chain_metrics(self):
        service = CrossChainAnalyticsService()
        m = service.get_chain_metrics("ethereum")
        assert m is not None
        assert m.chain == "ethereum"
        assert m.total_transfers > 0

    def test_list_chain_metrics(self):
        service = CrossChainAnalyticsService()
        metrics = service.list_chain_metrics()
        assert len(metrics) >= 5

    def test_metrics_updates(self):
        service = CrossChainAnalyticsService()
        before = service.get_chain_metrics("ethereum")
        service.record_transfer("ethereum", "verdis", "VRS", 5000, "0x1", "0x2")
        after = service.get_chain_metrics("ethereum")
        assert after.total_transfers >= before.total_transfers


class TestCorridors:
    def test_list_corridors(self):
        service = CrossChainAnalyticsService()
        corridors = service.list_corridors()
        assert len(corridors) > 0

    def test_get_corridor(self):
        service = CrossChainAnalyticsService()
        service.record_transfer("ethereum", "verdis", "VRS", 1000, "0x1", "0x2")
        c = service.get_corridor("ethereum", "verdis")
        assert c is not None
        assert c.transfer_count > 0

    def test_corridor_volume(self):
        service = CrossChainAnalyticsService()
        service.record_transfer("ethereum", "verdis", "VRS", 1000, "0x1", "0x2")
        c = service.get_corridor("ethereum", "verdis")
        assert c.total_volume > 0


class TestFlowAnalysis:
    def test_flow_24h(self):
        service = CrossChainAnalyticsService()
        flow = service.get_flow_analysis(24)
        assert "total_transfers" in flow
        assert "inflows" in flow
        assert "outflows" in flow
        assert "net_flows" in flow

    def test_flow_7d(self):
        service = CrossChainAnalyticsService()
        flow = service.get_flow_analysis(168)
        assert flow["period_hours"] == 168

    def test_flow_by_token(self):
        service = CrossChainAnalyticsService()
        flow = service.get_flow_analysis(720)
        assert "by_token" in flow


class TestTrends:
    def test_volume_trend(self):
        service = CrossChainAnalyticsService()
        trend = service.get_volume_trend(7)
        assert len(trend) == 7
        assert all("date" in d and "volume" in d for d in trend)

    def test_volume_trend_30d(self):
        service = CrossChainAnalyticsService()
        trend = service.get_volume_trend(30)
        assert len(trend) == 30


class TestTokenDistribution:
    def test_token_distribution(self):
        service = CrossChainAnalyticsService()
        dist = service.get_token_distribution()
        assert len(dist) > 0
        assert all("token" in d and "total_volume" in d for d in dist)

    def test_token_distribution_sorted(self):
        service = CrossChainAnalyticsService()
        dist = service.get_token_distribution()
        volumes = [d["total_volume"] for d in dist]
        assert volumes == sorted(volumes, reverse=True)


class TestComparison:
    def test_compare_all_chains(self):
        service = CrossChainAnalyticsService()
        comparison = service.compare_chains()
        assert len(comparison) >= 5
        assert all("net_flow" in c for c in comparison)

    def test_compare_specific_chains(self):
        service = CrossChainAnalyticsService()
        comparison = service.compare_chains(["ethereum", "verdis"])
        assert len(comparison) == 2


class TestStats:
    def test_stats(self):
        service = CrossChainAnalyticsService()
        stats = service.get_stats()
        assert stats["total_transfers"] > 0
        assert stats["total_volume"] > 0
        assert "success_rate" in stats

    def test_dashboard(self):
        service = CrossChainAnalyticsService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "flow_24h" in dash
        assert "volume_trend" in dash
        assert "chain_comparison" in dash
        assert "top_corridors" in dash
        assert "token_distribution" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = CrossChainAnalyticsService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestCrossChainAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "stats" in resp.json()

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_transfers"] > 0

    def test_list_transfers(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/transfers", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_record_transfer(self, client, test_user):
        resp = client.post("/api/v1/cross-chain/transfers", json={
            "source_chain": "ethereum", "target_chain": "verdis",
            "token": "VRS", "amount": 5000, "sender": "0x1", "recipient": "0x2",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("xfer-")

    def test_chains(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/chains", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 5

    def test_chain_metrics(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/chains/metrics", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 5

    def test_corridors(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/corridors", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_flow(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/flow?hours=24", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_transfers" in resp.json()

    def test_volume_trend(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/trends/volume?days=7", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) == 7

    def test_token_distribution(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/tokens/distribution", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_compare_chains(self, client, test_user):
        resp = client.get("/api/v1/cross-chain/chains/compare", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 5

    def test_singleton(self):
        assert get_cross_chain_analytics_service() is get_cross_chain_analytics_service()
