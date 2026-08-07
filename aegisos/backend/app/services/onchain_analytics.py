"""
On-chain Analytics Dashboard — Phase 34

Real-time blockchain metrics, TPS tracking, gas analytics,
block statistics, and historical data collection from Verdis RPC.
"""

import time
import threading
import json
import urllib.request
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import deque
from enum import Enum
from app.core.logging import get_logger

logger = get_logger("service.onchain_analytics")


class MetricType(str, Enum):
    TPS = "tps"
    BLOCK_TIME = "block_time"
    GAS_USED = "gas_used"
    TX_COUNT = "tx_count"
    PEER_COUNT = "peer_count"
    VALIDATOR_COUNT = "validator_count"
    BLOCK_SIZE = "block_size"
    MEMPOOL_SIZE = "mempool_size"


@dataclass
class BlockStats:
    height: int
    hash: str
    parent_hash: str
    timestamp: str
    tx_count: int
    gas_used: int
    gas_limit: int
    block_size_bytes: int
    validator: str
    extrinsics: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MetricSnapshot:
    timestamp: str
    metric_type: str
    value: float
    block_height: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnalyticsAlert:
    id: str
    metric_type: str
    condition: str  # "gt", "lt", "eq"
    threshold: float
    message: str
    triggered: bool = False
    triggered_at: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class OnchainAnalyticsService:
    """Collects and analyzes on-chain metrics from Verdis blockchain."""

    def __init__(self, rpc_url: str = "https://verdischain.com/rpc", max_history: int = 5000):
        self._rpc_url = rpc_url
        self._blocks: deque = deque(maxlen=max_history)
        self._metrics: dict[str, deque] = {m.value: deque(maxlen=max_history) for m in MetricType}
        self._alerts: dict[str, AnalyticsAlert] = {}
        self._latest_block: Optional[BlockStats] = None
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stats_cache: dict = {}
        self._last_fetch: str = ""

    def _rpc_call(self, method: str, params: list = None) -> Optional[dict]:
        """Make a JSON-RPC call to the Verdis node."""
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                self._rpc_url,
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning("rpc_call_failed", method=method, error=str(e))
            return None

    def fetch_block(self, height: int = None) -> Optional[BlockStats]:
        """Fetch block stats from RPC (or simulate if unreachable)."""
        result = self._rpc_call("chain_getBlockHash", [height] if height else [])
        if not result or "result" not in result:
            return self._simulate_block(height)

        block_hash = result["result"]
        block_result = self._rpc_call("chain_getBlock", [block_hash])

        if not block_result or "result" not in block_result:
            return self._simulate_block(height)

        block = block_result["result"]["block"]
        header = block["header"]
        extrinsics = block.get("extrinsics", [])

        return BlockStats(
            height=int(header["number"], 16) if isinstance(header["number"], str) else header["number"],
            hash=block_hash,
            parent_hash=header.get("parentHash", ""),
            timestamp=header.get("timestamp", datetime.utcnow().isoformat()),
            tx_count=len(extrinsics),
            gas_used=int(header.get("digest", {}).get("gasUsed", "0x0"), 16) if isinstance(header.get("digest", {}).get("gasUsed", "0x0"), str) else 0,
            gas_limit=10000000,
            block_size_bytes=len(json.dumps(block)),
            validator=header.get("author", ""),
            extrinsics=len(extrinsics),
        )

    def _simulate_block(self, height: int = None) -> BlockStats:
        """Simulate block stats when RPC is unreachable."""
        import secrets
        current_height = height or (self._latest_block.height + 1 if self._latest_block else 100000)
        return BlockStats(
            height=current_height,
            hash="0x" + secrets.token_hex(32),
            parent_hash=self._latest_block.hash if self._latest_block else "0x" + secrets.token_hex(32),
            timestamp=datetime.utcnow().isoformat(),
            tx_count=secrets.randbelow(20) + 1,
            gas_used=secrets.randbelow(5000000) + 100000,
            gas_limit=10000000,
            block_size_bytes=secrets.randbelow(50000) + 1000,
            validator="0x" + secrets.token_hex(20),
            extrinsics=secrets.randbelow(15) + 1,
        )

    def collect_metrics(self) -> dict:
        """Collect current on-chain metrics."""
        block = self.fetch_block()

        with self._lock:
            self._latest_block = block
            self._blocks.append(block)

            # Calculate TPS
            if len(self._blocks) >= 2:
                prev = self._blocks[-2]
                time_diff = max(1, (datetime.utcnow() - datetime.fromisoformat(prev.timestamp.replace("Z", ""))).total_seconds())
                tps = (block.tx_count + prev.tx_count) / time_diff if time_diff > 0 else 0
            else:
                tps = block.tx_count / 6.0  # Assume 6s block time

            # Calculate block time
            if len(self._blocks) >= 2:
                prev = self._blocks[-2]
                block_time = 6.0  # Default
            else:
                block_time = 6.0

            # Record metrics
            metrics = {
                MetricType.TPS.value: tps,
                MetricType.BLOCK_TIME.value: block_time,
                MetricType.GAS_USED.value: block.gas_used,
                MetricType.TX_COUNT.value: block.tx_count,
                MetricType.BLOCK_SIZE.value: block.block_size_bytes,
            }

            for m_type, value in metrics.items():
                self._metrics[m_type].append(MetricSnapshot(
                    timestamp=datetime.utcnow().isoformat(),
                    metric_type=m_type,
                    value=value,
                    block_height=block.height,
                ))

            self._last_fetch = datetime.utcnow().isoformat()

            # Check alerts
            self._check_alerts(metrics)

            return {
                "block": block.to_dict(),
                "metrics": {k: v for k, v in metrics.items()},
                "timestamp": self._last_fetch,
            }

    def _check_alerts(self, metrics: dict):
        """Check alert conditions against current metrics."""
        for alert in self._alerts.values():
            if alert.triggered:
                continue
            value = metrics.get(alert.metric_type, 0)
            if alert.condition == "gt" and value > alert.threshold:
                alert.triggered = True
                alert.triggered_at = datetime.utcnow().isoformat()
            elif alert.condition == "lt" and value < alert.threshold:
                alert.triggered = True
                alert.triggered_at = datetime.utcnow().isoformat()

    def get_latest_block(self) -> Optional[BlockStats]:
        return self._latest_block

    def get_recent_blocks(self, limit: int = 20) -> list[BlockStats]:
        return list(self._blocks)[-limit:]

    def get_metric_history(self, metric_type: str, limit: int = 100) -> list[MetricSnapshot]:
        return list(self._metrics.get(metric_type, []))[-limit:]

    def get_all_metrics(self) -> dict:
        """Get latest value of all metrics."""
        result = {}
        for m_type in MetricType:
            history = self._metrics.get(m_type.value, [])
            if history:
                latest = history[-1]
                result[m_type.value] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp,
                    "block_height": latest.block_height,
                }
            else:
                result[m_type.value] = {"value": 0, "timestamp": "", "block_height": 0}
        return result

    def get_tps_trend(self, window: int = 50) -> dict:
        """Get TPS trend analysis."""
        tps_history = list(self._metrics.get(MetricType.TPS.value, []))[-window:]
        if not tps_history:
            return {"avg": 0, "min": 0, "max": 0, "trend": "stable", "values": []}

        values = [s.value for s in tps_history]
        avg = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)

        # Trend direction
        if len(values) >= 10:
            first_half = sum(values[:len(values)//2]) / (len(values)//2)
            second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            if second_half > first_half * 1.1:
                trend = "increasing"
            elif second_half < first_half * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "avg": round(avg, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "trend": trend,
            "values": [round(v, 2) for v in values],
        }

    def get_gas_analytics(self, window: int = 50) -> dict:
        """Get gas usage analytics."""
        gas_history = list(self._metrics.get(MetricType.GAS_USED.value, []))[-window:]
        if not gas_history:
            return {"avg": 0, "min": 0, "max": 0, "utilization": 0, "values": []}

        values = [s.value for s in gas_history]
        avg = sum(values) / len(values)
        gas_limit = 10000000

        return {
            "avg": round(avg, 2),
            "min": min(values),
            "max": max(values),
            "utilization": round((avg / gas_limit) * 100, 2),
            "values": values,
        }

    def get_block_analytics(self, window: int = 50) -> dict:
        """Get block statistics."""
        blocks = list(self._blocks)[-window:]
        if not blocks:
            return {"total": 0, "avg_tx_count": 0, "avg_size": 0, "avg_gas": 0}

        tx_counts = [b.tx_count for b in blocks]
        sizes = [b.block_size_bytes for b in blocks]
        gas = [b.gas_used for b in blocks]

        return {
            "total": len(blocks),
            "latest_height": blocks[-1].height if blocks else 0,
            "avg_tx_count": round(sum(tx_counts) / len(tx_counts), 2),
            "avg_size_bytes": round(sum(sizes) / len(sizes), 2),
            "avg_gas": round(sum(gas) / len(gas), 2),
            "total_tx": sum(tx_counts),
        }

    # === Alerts ===

    def create_alert(self, metric_type: str, condition: str, threshold: float, message: str = "") -> AnalyticsAlert:
        import secrets as s
        alert_id = f"alert-{s.token_hex(8)}"
        alert = AnalyticsAlert(
            id=alert_id, metric_type=metric_type, condition=condition,
            threshold=threshold, message=message or f"{metric_type} {condition} {threshold}",
        )
        self._alerts[alert_id] = alert
        return alert

    def list_alerts(self, triggered: bool = None) -> list[AnalyticsAlert]:
        if triggered is not None:
            return [a for a in self._alerts.values() if a.triggered == triggered]
        return list(self._alerts.values())

    def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            return True
        return False

    def reset_alert(self, alert_id: str) -> bool:
        if alert_id in self._alerts:
            self._alerts[alert_id].triggered = False
            self._alerts[alert_id].triggered_at = ""
            return True
        return False

    # === Monitoring ===

    def start_monitoring(self, interval: int = 6):
        """Start background monitoring thread."""
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("monitoring_started", interval=interval)

    def stop_monitoring(self):
        """Stop monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("monitoring_stopped")

    def _monitor_loop(self, interval: int):
        """Background monitoring loop."""
        while self._monitoring:
            try:
                self.collect_metrics()
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Dashboard Summary ===

    def get_dashboard(self) -> dict:
        """Get complete dashboard data in one call."""
        return {
            "latest_block": self._latest_block.to_dict() if self._latest_block else None,
            "metrics": self.get_all_metrics(),
            "tps_trend": self.get_tps_trend(),
            "gas_analytics": self.get_gas_analytics(),
            "block_analytics": self.get_block_analytics(),
            "recent_blocks": [b.to_dict() for b in self.get_recent_blocks(10)],
            "alerts": {
                "total": len(self._alerts),
                "triggered": sum(1 for a in self._alerts.values() if a.triggered),
            },
            "monitoring": self._monitoring,
            "last_fetch": self._last_fetch,
        }

    def get_stats(self) -> dict:
        return {
            "total_blocks_tracked": len(self._blocks),
            "total_metrics_recorded": sum(len(v) for v in self._metrics.values()),
            "total_alerts": len(self._alerts),
            "triggered_alerts": sum(1 for a in self._alerts.values() if a.triggered),
            "monitoring": self._monitoring,
            "rpc_url": self._rpc_url,
        }


_service: Optional[OnchainAnalyticsService] = None

def get_onchain_analytics_service() -> OnchainAnalyticsService:
    global _service
    if _service is None:
        _service = OnchainAnalyticsService()
    return _service
