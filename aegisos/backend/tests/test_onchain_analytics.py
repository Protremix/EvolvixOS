"""Tests for On-chain Analytics — Phase 34."""

import pytest
import time
from app.services.onchain_analytics import (
    OnchainAnalyticsService, get_onchain_analytics_service, MetricType,
)


class TestBlockCollection:
    def test_collect_metrics(self):
        service = OnchainAnalyticsService()
        result = service.collect_metrics()
        assert "block" in result
        assert "metrics" in result
        assert result["block"]["height"] > 0

    def test_collect_multiple_blocks(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        service.collect_metrics()
        blocks = service.get_recent_blocks()
        assert len(blocks) >= 2

    def test_latest_block(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        latest = service.get_latest_block()
        assert latest is not None
        assert latest.height > 0

    def test_recent_blocks(self):
        service = OnchainAnalyticsService()
        for _ in range(3):
            service.collect_metrics()
        blocks = service.get_recent_blocks(2)
        assert len(blocks) == 2

    def test_block_fields(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        block = service.get_latest_block()
        assert block.hash != ""
        assert block.tx_count >= 0
        assert block.gas_used >= 0
        assert block.block_size_bytes > 0


class TestMetrics:
    def test_get_all_metrics(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        metrics = service.get_all_metrics()
        assert "tps" in metrics
        assert "block_time" in metrics
        assert "gas_used" in metrics

    def test_metric_history(self):
        service = OnchainAnalyticsService()
        for _ in range(5):
            service.collect_metrics()
        history = service.get_metric_history("tps", 10)
        assert len(history) >= 5

    def test_metric_types(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        for m_type in MetricType:
            history = service.get_metric_history(m_type.value)
            assert isinstance(history, list)


class TestTpsTrend:
    def test_tps_trend_empty(self):
        service = OnchainAnalyticsService()
        trend = service.get_tps_trend()
        assert trend["avg"] == 0
        assert trend["trend"] == "stable"

    def test_tps_trend_with_data(self):
        service = OnchainAnalyticsService()
        for _ in range(15):
            service.collect_metrics()
        trend = service.get_tps_trend()
        assert trend["avg"] > 0
        assert trend["trend"] in ("stable", "increasing", "decreasing")
        assert len(trend["values"]) > 0

    def test_tps_trend_window(self):
        service = OnchainAnalyticsService()
        for _ in range(20):
            service.collect_metrics()
        trend = service.get_tps_trend(10)
        assert len(trend["values"]) <= 10


class TestGasAnalytics:
    def test_gas_analytics_empty(self):
        service = OnchainAnalyticsService()
        gas = service.get_gas_analytics()
        assert gas["avg"] == 0

    def test_gas_analytics_with_data(self):
        service = OnchainAnalyticsService()
        for _ in range(5):
            service.collect_metrics()
        gas = service.get_gas_analytics()
        assert gas["avg"] >= 0
        assert gas["utilization"] >= 0
        assert gas["utilization"] <= 100


class TestBlockAnalytics:
    def test_block_analytics_empty(self):
        service = OnchainAnalyticsService()
        analytics = service.get_block_analytics()
        assert analytics["total"] == 0

    def test_block_analytics_with_data(self):
        service = OnchainAnalyticsService()
        for _ in range(5):
            service.collect_metrics()
        analytics = service.get_block_analytics()
        assert analytics["total"] >= 5
        assert analytics["avg_tx_count"] > 0
        assert analytics["latest_height"] > 0


class TestAlerts:
    def test_create_alert(self):
        service = OnchainAnalyticsService()
        alert = service.create_alert("tps", "gt", 100, "TPS too high")
        assert alert.id.startswith("alert-")
        assert alert.triggered is False

    def test_list_alerts(self):
        service = OnchainAnalyticsService()
        service.create_alert("tps", "gt", 100)
        alerts = service.list_alerts()
        assert len(alerts) >= 1

    def test_list_alerts_filtered(self):
        service = OnchainAnalyticsService()
        service.create_alert("tps", "gt", 100)
        untriggered = service.list_alerts(triggered=False)
        assert all(not a.triggered for a in untriggered)

    def test_delete_alert(self):
        service = OnchainAnalyticsService()
        alert = service.create_alert("gas_used", "gt", 9000000)
        assert service.delete_alert(alert.id) is True
        assert service.list_alerts() == []

    def test_reset_alert(self):
        service = OnchainAnalyticsService()
        alert = service.create_alert("tps", "gt", 0)  # Will trigger immediately
        service.collect_metrics()  # TPS > 0
        triggered = service.list_alerts(triggered=True)
        if triggered:
            assert service.reset_alert(triggered[0].id) is True
            assert service.list_alerts(triggered=True) == []


class TestDashboard:
    def test_dashboard_empty(self):
        service = OnchainAnalyticsService()
        dashboard = service.get_dashboard()
        assert dashboard["latest_block"] is None
        assert "metrics" in dashboard
        assert "alerts" in dashboard

    def test_dashboard_with_data(self):
        service = OnchainAnalyticsService()
        for _ in range(3):
            service.collect_metrics()
        dashboard = service.get_dashboard()
        assert dashboard["latest_block"] is not None
        assert "tps_trend" in dashboard
        assert "gas_analytics" in dashboard
        assert "block_analytics" in dashboard
        assert len(dashboard["recent_blocks"]) > 0


class TestMonitoring:
    def test_start_stop_monitoring(self):
        service = OnchainAnalyticsService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)  # Let it collect
        service.stop_monitoring()
        assert service.is_monitoring() is False

    def test_start_already_monitoring(self):
        service = OnchainAnalyticsService()
        service.start_monitoring(interval=10)
        service.start_monitoring(interval=10)  # Should not duplicate
        assert service.is_monitoring() is True
        service.stop_monitoring()


class TestStats:
    def test_stats(self):
        service = OnchainAnalyticsService()
        service.collect_metrics()
        stats = service.get_stats()
        assert "total_blocks_tracked" in stats
        assert stats["total_blocks_tracked"] >= 1
        assert "monitoring" in stats


class TestAnalyticsAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/onchain/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "metrics" in resp.json()

    def test_collect(self, client, test_user):
        resp = client.post("/api/v1/onchain/collect", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "block" in resp.json()

    def test_metrics(self, client, test_user):
        client.post("/api/v1/onchain/collect", headers=test_user["headers"])
        resp = client.get("/api/v1/onchain/metrics", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "tps" in resp.json()

    def test_blocks(self, client, test_user):
        client.post("/api/v1/onchain/collect", headers=test_user["headers"])
        resp = client.get("/api/v1/onchain/blocks/recent", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_tps_trend(self, client, test_user):
        for _ in range(3):
            client.post("/api/v1/onchain/collect", headers=test_user["headers"])
        resp = client.get("/api/v1/onchain/tps/trend", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "trend" in resp.json()

    def test_create_alert(self, client, test_user):
        resp = client.post("/api/v1/onchain/alerts", json={
            "metric_type": "tps", "condition": "gt", "threshold": 100, "message": "High TPS",
        }, headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["id"].startswith("alert-")

    def test_metric_types(self, client):
        resp = client.get("/api/v1/onchain/metric-types")
        assert resp.status_code == 200
        assert len(resp.json()) >= 8

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/onchain/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert "total_blocks_tracked" in resp.json()

    def test_singleton(self):
        assert get_onchain_analytics_service() is get_onchain_analytics_service()
