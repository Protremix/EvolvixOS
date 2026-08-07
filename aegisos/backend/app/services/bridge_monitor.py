"""
Bridge Monitoring — Phase 38

Cross-chain transaction tracking, bridge health metrics,
relayer status, anomaly detection, and alerting.
"""

import secrets
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.bridge_monitor")


class BridgeStatus(str, Enum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DOWN = "down"


class TransferStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    EXECUTED = "executed"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class TransferDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ChainType(str, Enum):
    ETHEREUM = "ethereum"
    VERDIS = "verdis"
    BSC = "bsc"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"


@dataclass
class BridgeTransfer:
    id: str
    direction: str
    source_chain: str
    target_chain: str
    sender: str
    recipient: str
    amount: float
    token: str
    status: str = TransferStatus.PENDING.value
    tx_hash_source: str = ""
    tx_hash_target: str = ""
    validator_signatures: int = 0
    required_signatures: int = 3
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    executed_at: str = ""
    error: str = ""
    block_height_source: int = 0
    block_height_target: int = 0
    fee: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RelayerStatus:
    id: str
    address: str
    name: str
    active: bool = True
    transfers_relayed: int = 0
    success_rate: float = 100.0
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    uptime_pct: float = 100.0
    latency_ms: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BridgeAlert:
    id: str
    alert_type: str  # high_failure_rate, large_transfer, stalled_transfer, relayer_down
    severity: str  # critical, high, medium, low
    message: str
    transfer_id: str = ""
    triggered: bool = False
    triggered_at: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    threshold: float = 0.0
    current_value: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class BridgeMonitorService:
    """Bridge monitoring, cross-chain transfer tracking, and alerting."""

    def __init__(self, max_history: int = 5000, required_signatures: int = 3):
        self._transfers: dict[str, BridgeTransfer] = {}
        _transfer_history: deque = deque(maxlen=max_history)
        self._relayers: dict[str, RelayerStatus] = {}
        self._alerts: dict[str, BridgeAlert] = {}
        self._lock = threading.Lock()
        self._required_signatures = required_signatures
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._bridge_status = BridgeStatus.OPERATIONAL.value
        self._total_volume = 0.0
        self._total_fees = 0.0
        self._init_default_relayers()
        self._init_default_alerts()

    def _init_default_relayers(self):
        """Initialize 3 default relayers."""
        for i in range(1, 4):
            rid = f"relayer-{i}"
            self._relayers[rid] = RelayerStatus(
                id=rid, address=f"0x{'b' * 38}{i:02d}",
                name=f"Verdis Relayer #{i}",
                latency_ms=50.0 + (i * 10),
            )

    def _init_default_alerts(self):
        """Initialize default monitoring alerts."""
        self.create_alert("high_failure_rate", "high", "Failure rate > 10%", threshold=10.0)
        self.create_alert("large_transfer", "medium", "Transfer > 1M VRS", threshold=1_000_000)
        self.create_alert("stalled_transfer", "high", "Transfer pending > 1 hour", threshold=3600)
        self.create_alert("relayer_down", "critical", "Relayer offline", threshold=0)

    # === Transfers ===

    def create_transfer(
        self, direction: str, source_chain: str, target_chain: str,
        sender: str, recipient: str, amount: float, token: str = "VRS",
        tx_hash_source: str = "", block_height_source: int = 0, fee: float = 0.0,
    ) -> BridgeTransfer:
        """Create a new bridge transfer."""
        transfer_id = f"br-{secrets.token_hex(8)}"
        transfer = BridgeTransfer(
            id=transfer_id, direction=direction,
            source_chain=source_chain, target_chain=target_chain,
            sender=sender, recipient=recipient, amount=amount,
            token=token, tx_hash_source=tx_hash_source,
            block_height_source=block_height_source, fee=fee,
            required_signatures=self._required_signatures,
        )
        self._transfers[transfer_id] = transfer
        self._total_volume += amount
        self._total_fees += fee

        # Check alerts
        self._check_large_transfer_alert(transfer)
        logger.info("transfer_created", id=transfer_id, direction=direction, amount=amount)
        return transfer

    def get_transfer(self, transfer_id: str) -> Optional[BridgeTransfer]:
        return self._transfers.get(transfer_id)

    def list_transfers(
        self, status: str = None, direction: str = None,
        source_chain: str = None, target_chain: str = None,
        limit: int = 50,
    ) -> list[BridgeTransfer]:
        transfers = list(self._transfers.values())
        if status:
            transfers = [t for t in transfers if t.status == status]
        if direction:
            transfers = [t for t in transfers if t.direction == direction]
        if source_chain:
            transfers = [t for t in transfers if t.source_chain == source_chain]
        if target_chain:
            transfers = [t for t in transfers if t.target_chain == target_chain]
        transfers.sort(key=lambda t: t.created, reverse=True)
        return transfers[:limit]

    def validate_transfer(self, transfer_id: str, relayer_id: str) -> Optional[BridgeTransfer]:
        """Add a validator signature to a transfer."""
        transfer = self._transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.PENDING.value:
            return None

        transfer.validator_signatures += 1
        transfer.updated = datetime.utcnow().isoformat()

        # Update relayer stats
        if relayer_id in self._relayers:
            self._relayers[relayer_id].transfers_relayed += 1
            self._relayers[relayer_id].last_active = datetime.utcnow().isoformat()

        if transfer.validator_signatures >= transfer.required_signatures:
            transfer.status = TransferStatus.VALIDATED.value

        return transfer

    def execute_transfer(self, transfer_id: str, tx_hash_target: str = "", block_height_target: int = 0) -> Optional[BridgeTransfer]:
        """Execute a validated transfer."""
        transfer = self._transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.VALIDATED.value:
            return None

        transfer.status = TransferStatus.EXECUTED.value
        transfer.tx_hash_target = tx_hash_target
        transfer.block_height_target = block_height_target
        transfer.executed_at = datetime.utcnow().isoformat()
        transfer.updated = datetime.utcnow().isoformat()

        logger.info("transfer_executed", id=transfer_id, target_tx=tx_hash_target)
        return transfer

    def fail_transfer(self, transfer_id: str, error: str = "") -> Optional[BridgeTransfer]:
        """Mark a transfer as failed."""
        transfer = self._transfers.get(transfer_id)
        if not transfer:
            return None
        transfer.status = TransferStatus.FAILED.value
        transfer.error = error
        transfer.updated = datetime.utcnow().isoformat()
        self._check_failure_rate_alert()
        return transfer

    def refund_transfer(self, transfer_id: str) -> Optional[BridgeTransfer]:
        """Refund a failed transfer."""
        transfer = self._transfers.get(transfer_id)
        if not transfer or transfer.status != TransferStatus.FAILED.value:
            return None
        transfer.status = TransferStatus.REFUNDED.value
        transfer.updated = datetime.utcnow().isoformat()
        return transfer

    # === Relayers ===

    def register_relayer(self, address: str, name: str) -> RelayerStatus:
        rid = f"relayer-{secrets.token_hex(4)}"
        relayer = RelayerStatus(id=rid, address=address, name=name)
        self._relayers[rid] = relayer
        return relayer

    def remove_relayer(self, relayer_id: str) -> bool:
        if relayer_id in self._relayers:
            self._relayers[relayer_id].active = False
            self._check_relayer_alerts()
            return True
        return False

    def activate_relayer(self, relayer_id: str) -> bool:
        if relayer_id in self._relayers:
            self._relayers[relayer_id].active = True
            return True
        return False

    def get_relayer(self, relayer_id: str) -> Optional[RelayerStatus]:
        return self._relayers.get(relayer_id)

    def list_relayers(self, active_only: bool = True) -> list[RelayerStatus]:
        relayers = list(self._relayers.values())
        if active_only:
            relayers = [r for r in relayers if r.active]
        return relayers

    def update_relayer_stats(self, relayer_id: str, latency_ms: float = None, success_rate: float = None):
        r = self._relayers.get(relayer_id)
        if not r:
            return
        if latency_ms is not None:
            r.latency_ms = latency_ms
        if success_rate is not None:
            r.success_rate = success_rate

    # === Alerts ===

    def create_alert(self, alert_type: str, severity: str, message: str, threshold: float = 0) -> BridgeAlert:
        aid = f"alert-{secrets.token_hex(8)}"
        alert = BridgeAlert(
            id=aid, alert_type=alert_type, severity=severity,
            message=message, threshold=threshold,
        )
        self._alerts[aid] = alert
        return alert

    def list_alerts(self, triggered: bool = None) -> list[BridgeAlert]:
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

    def _check_large_transfer_alert(self, transfer: BridgeTransfer):
        for alert in self._alerts.values():
            if alert.alert_type == "large_transfer" and not alert.triggered:
                if transfer.amount > alert.threshold:
                    alert.triggered = True
                    alert.triggered_at = datetime.utcnow().isoformat()
                    alert.current_value = transfer.amount
                    alert.transfer_id = transfer.id

    def _check_failure_rate_alert(self):
        stats = self.get_transfer_stats()
        failure_rate = stats.get("failure_rate", 0)
        for alert in self._alerts.values():
            if alert.alert_type == "high_failure_rate" and not alert.triggered:
                if failure_rate > alert.threshold:
                    alert.triggered = True
                    alert.triggered_at = datetime.utcnow().isoformat()
                    alert.current_value = failure_rate

    def _check_relayer_alerts(self):
        active = sum(1 for r in self._relayers.values() if r.active)
        for alert in self._alerts.values():
            if alert.alert_type == "relayer_down" and not alert.triggered:
                if active <= alert.threshold:
                    alert.triggered = True
                    alert.triggered_at = datetime.utcnow().isoformat()
                    alert.current_value = active

    def _check_stalled_transfers(self):
        now = datetime.utcnow()
        for transfer in self._transfers.values():
            if transfer.status == TransferStatus.PENDING.value:
                age = (now - datetime.fromisoformat(transfer.created.replace("Z", ""))).total_seconds()
                for alert in self._alerts.values():
                    if alert.alert_type == "stalled_transfer" and not alert.triggered:
                        if age > alert.threshold:
                            alert.triggered = True
                            alert.triggered_at = datetime.utcnow().isoformat()
                            alert.current_value = age
                            alert.transfer_id = transfer.id

    # === Stats ===

    def get_transfer_stats(self) -> dict:
        transfers = list(self._transfers.values())
        total = len(transfers)
        by_status = defaultdict(int)
        by_direction = defaultdict(int)
        by_chain = defaultdict(int)
        executed = 0
        failed = 0

        for t in transfers:
            by_status[t.status] += 1
            by_direction[t.direction] += 1
            by_chain[t.source_chain] += 1
            if t.status == TransferStatus.EXECUTED.value:
                executed += 1
            elif t.status == TransferStatus.FAILED.value:
                failed += 1

        success_rate = (executed / max(1, executed + failed)) * 100 if (executed + failed) > 0 else 100.0
        failure_rate = (failed / max(1, total)) * 100 if total > 0 else 0.0

        return {
            "total_transfers": total,
            "executed": executed,
            "failed": failed,
            "pending": by_status.get("pending", 0),
            "validated": by_status.get("validated", 0),
            "success_rate": round(success_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "total_volume": self._total_volume,
            "total_fees": self._total_fees,
            "by_status": dict(by_status),
            "by_direction": dict(by_direction),
            "by_source_chain": dict(by_chain),
        }

    def get_bridge_health(self) -> dict:
        stats = self.get_transfer_stats()
        active_relayers = sum(1 for r in self._relayers.values() if r.active)
        total_relayers = len(self._relayers)
        avg_latency = sum(r.latency_ms for r in self._relayers.values()) / max(1, len(self._relayers))

        if active_relayers == 0:
            status = BridgeStatus.DOWN.value
        elif active_relayers < total_relayers / 2 or stats["failure_rate"] > 10:
            status = BridgeStatus.DEGRADED.value
        else:
            status = BridgeStatus.OPERATIONAL.value

        self._bridge_status = status

        return {
            "status": status,
            "active_relayers": active_relayers,
            "total_relayers": total_relayers,
            "avg_latency_ms": round(avg_latency, 2),
            "success_rate": stats["success_rate"],
            "failure_rate": stats["failure_rate"],
            "total_transfers": stats["total_transfers"],
            "total_volume": self._total_volume,
            "total_fees": self._total_fees,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 10):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("bridge_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                self._check_stalled_transfers()
                self._check_relayer_alerts()
                self.get_bridge_health()
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "health": self.get_bridge_health(),
            "transfer_stats": self.get_transfer_stats(),
            "relayers": [r.to_dict() for r in self.list_relayers()],
            "recent_transfers": [t.to_dict() for t in self.list_transfers(limit=10)],
            "alerts": {
                "total": len(self._alerts),
                "triggered": sum(1 for a in self._alerts.values() if a.triggered),
            },
            "monitoring": self._monitoring,
        }


_service: Optional[BridgeMonitorService] = None

def get_bridge_monitor_service() -> BridgeMonitorService:
    global _service
    if _service is None:
        _service = BridgeMonitorService()
    return _service
