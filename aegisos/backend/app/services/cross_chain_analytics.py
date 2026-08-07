"""
Cross-Chain Analytics — Phase 42

Multi-chain interaction tracking, flow analysis, volume trends,
corridor analytics, and cross-chain comparison across blockchain networks.
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

logger = get_logger("service.cross_chain_analytics")


class ChainType(str, Enum):
    ETHEREUM = "ethereum"
    VERDIS = "verdis"
    BSC = "bsc"
    POLYGON = "polygon"
    AVALANCHE = "avalanche"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    SOLANA = "solana"


class FlowDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class CrossChainTransfer:
    id: str
    source_chain: str
    target_chain: str
    token: str
    amount: float
    sender: str
    recipient: str
    bridge_protocol: str = "verdis-bridge"
    status: str = "confirmed"
    tx_hash_source: str = ""
    tx_hash_target: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    block_number: int = 0
    gas_paid: float = 0.0
    duration_seconds: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ChainMetrics:
    chain: str
    total_transfers: int = 0
    total_volume: float = 0.0
    inbound_volume: float = 0.0
    outbound_volume: float = 0.0
    active_addresses: int = 0
    avg_transfer_size: float = 0.0
    avg_duration: float = 0.0
    success_rate: float = 100.0
    last_activity: str = ""
    tps: float = 0.0
    gas_price: float = 0.0
    bridge_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CorridorStats:
    source_chain: str
    target_chain: str
    transfer_count: int = 0
    total_volume: float = 0.0
    avg_transfer_size: float = 0.0
    avg_duration: float = 0.0
    success_rate: float = 100.0
    last_transfer: str = ""
    token_breakdown: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class CrossChainAnalyticsService:
    """Cross-chain analytics with transfer tracking, flow analysis, and chain comparison."""

    def __init__(self, max_history: int = 10000):
        self._transfers: dict[str, CrossChainTransfer] = {}
        self._chain_metrics: dict[str, ChainMetrics] = {}
        self._corridors: dict[str, CorridorStats] = {}
        self._history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_chains()
        self._init_sample_transfers()

    def _init_chains(self):
        """Initialize chain metrics for all supported chains."""
        for chain in ChainType:
            self._chain_metrics[chain.value] = ChainMetrics(chain=chain.value)

    def _init_sample_transfers(self):
        """Initialize with sample cross-chain transfers."""
        import random
        random.seed(42)
        chains = [c.value for c in ChainType]
        tokens = ["VRS", "ETH", "USDC", "USDT", "WBTC", "VRDX"]
        bridges = ["verdis-bridge", "wormhole", "layerzero", "axelar"]

        for i in range(200):
            source = random.choice(chains)
            target = random.choice([c for c in chains if c != source])
            token = random.choice(tokens)
            amount = random.uniform(100, 500000)
            duration = random.randint(2, 300)
            gas = random.uniform(0.5, 50)
            status = random.choices(["confirmed", "pending", "failed"], weights=[85, 10, 5])[0]
            bridge = random.choice(bridges)

            t = CrossChainTransfer(
                id=f"xfer-{secrets.token_hex(8)}",
                source_chain=source, target_chain=target, token=token,
                amount=round(amount, 2),
                sender=f"0x{secrets.token_hex(20)}",
                recipient=f"0x{secrets.token_hex(20)}",
                bridge_protocol=bridge, status=status,
                duration_seconds=duration,
                gas_paid=round(gas, 2),
                block_number=18000000 + i,
                timestamp=(datetime.utcnow() - timedelta(hours=random.randint(0, 720))).isoformat(),
            )
            self._transfers[t.id] = t
            self._history.append(t)
            self._update_metrics(t)
            self._update_corridor(t)

    def _update_metrics(self, transfer: CrossChainTransfer):
        """Update chain metrics from a transfer."""
        src = self._chain_metrics.get(transfer.source_chain)
        tgt = self._chain_metrics.get(transfer.target_chain)
        if src:
            src.total_transfers += 1
            src.outbound_volume += transfer.amount
            src.total_volume += transfer.amount
            src.last_activity = transfer.timestamp
            src.bridge_count = max(src.bridge_count, 1)
        if tgt:
            tgt.total_transfers += 1
            tgt.inbound_volume += transfer.amount
            tgt.total_volume += transfer.amount
            tgt.last_activity = transfer.timestamp

    def _update_corridor(self, transfer: CrossChainTransfer):
        """Update corridor stats from a transfer."""
        key = f"{transfer.source_chain}->{transfer.target_chain}"
        corridor = self._corridors.get(key)
        if not corridor:
            corridor = CorridorStats(
                source_chain=transfer.source_chain,
                target_chain=transfer.target_chain,
            )
            self._corridors[key] = corridor
        corridor.transfer_count += 1
        corridor.total_volume += transfer.amount
        corridor.avg_transfer_size = corridor.total_volume / corridor.transfer_count
        corridor.last_transfer = transfer.timestamp
        if transfer.token:
            corridor.token_breakdown[transfer.token] = corridor.token_breakdown.get(transfer.token, 0) + transfer.amount

    # === Record Transfer ===

    def record_transfer(
        self, source_chain: str, target_chain: str, token: str,
        amount: float, sender: str, recipient: str,
        bridge_protocol: str = "verdis-bridge", status: str = "confirmed",
        tx_hash_source: str = "", tx_hash_target: str = "",
        gas_paid: float = 0.0, duration_seconds: int = 0,
        block_number: int = 0, metadata: dict = None,
    ) -> CrossChainTransfer:
        """Record a new cross-chain transfer."""
        transfer_id = f"xfer-{secrets.token_hex(8)}"
        transfer = CrossChainTransfer(
            id=transfer_id, source_chain=source_chain, target_chain=target_chain,
            token=token, amount=amount, sender=sender, recipient=recipient,
            bridge_protocol=bridge_protocol, status=status,
            tx_hash_source=tx_hash_source, tx_hash_target=tx_hash_target,
            gas_paid=gas_paid, duration_seconds=duration_seconds,
            block_number=block_number, metadata=metadata or {},
        )

        with self._lock:
            self._transfers[transfer_id] = transfer
            self._history.append(transfer)
            self._update_metrics(transfer)
            self._update_corridor(transfer)

        logger.info("transfer_recorded", id=transfer_id, source=source_chain, target=target_chain, token=token, amount=amount)
        return transfer

    # === Queries ===

    def get_transfer(self, transfer_id: str) -> Optional[CrossChainTransfer]:
        return self._transfers.get(transfer_id)

    def list_transfers(
        self, source_chain: str = None, target_chain: str = None,
        token: str = None, status: str = None, bridge_protocol: str = None,
        min_amount: float = None, max_amount: float = None,
        limit: int = 50, sort_by: str = "timestamp",
    ) -> list[CrossChainTransfer]:
        transfers = list(self._transfers.values())
        if source_chain:
            transfers = [t for t in transfers if t.source_chain == source_chain]
        if target_chain:
            transfers = [t for t in transfers if t.target_chain == target_chain]
        if token:
            transfers = [t for t in transfers if t.token == token]
        if status:
            transfers = [t for t in transfers if t.status == status]
        if bridge_protocol:
            transfers = [t for t in transfers if t.bridge_protocol == bridge_protocol]
        if min_amount is not None:
            transfers = [t for t in transfers if t.amount >= min_amount]
        if max_amount is not None:
            transfers = [t for t in transfers if t.amount <= max_amount]

        sort_map = {
            "timestamp": lambda t: t.timestamp,
            "amount": lambda t: t.amount,
            "duration": lambda t: t.duration_seconds,
        }
        transfers.sort(key=sort_map.get(sort_by, lambda t: t.timestamp), reverse=True)
        return transfers[:limit]

    # === Chain Metrics ===

    def get_chain_metrics(self, chain: str) -> Optional[ChainMetrics]:
        m = self._chain_metrics.get(chain)
        if not m:
            return None
        # Calculate derived fields
        transfers = [t for t in self._transfers.values() if t.source_chain == chain or t.target_chain == chain]
        if transfers:
            m.active_addresses = len(set(t.sender for t in transfers))
            m.avg_transfer_size = m.total_volume / max(1, m.total_transfers)
            confirmed = [t for t in transfers if t.status == "confirmed"]
            m.success_rate = round(len(confirmed) / len(transfers) * 100, 2) if transfers else 100.0
            m.avg_duration = sum(t.duration_seconds for t in confirmed) / max(1, len(confirmed))
        return m

    def list_chain_metrics(self) -> list[ChainMetrics]:
        return [self.get_chain_metrics(c.value) for c in ChainType if self.get_chain_metrics(c.value)]

    # === Corridors ===

    def list_corridors(self, sort_by: str = "total_volume", limit: int = 50) -> list[CorridorStats]:
        corridors = list(self._corridors.values())
        sort_map = {
            "total_volume": lambda c: c.total_volume,
            "transfer_count": lambda c: c.transfer_count,
            "avg_transfer_size": lambda c: c.avg_transfer_size,
        }
        corridors.sort(key=sort_map.get(sort_by, lambda c: c.total_volume), reverse=True)
        return corridors[:limit]

    def get_corridor(self, source: str, target: str) -> Optional[CorridorStats]:
        return self._corridors.get(f"{source}->{target}")

    # === Flow Analysis ===

    def get_flow_analysis(self, hours: int = 24) -> dict:
        """Get cross-chain flow analysis for a time window."""
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        recent = [t for t in self._transfers.values() if t.timestamp >= cutoff]

        inflows = defaultdict(float)
        outflows = defaultdict(float)
        by_token = defaultdict(float)
        by_bridge = defaultdict(int)

        for t in recent:
            outflows[t.source_chain] += t.amount
            inflows[t.target_chain] += t.amount
            by_token[t.token] += t.amount
            by_bridge[t.bridge_protocol] += 1

        chains = set(list(inflows.keys()) + list(outflows.keys()))
        net_flows = {c: round(inflows.get(c, 0) - outflows.get(c, 0), 2) for c in chains}

        return {
            "period_hours": hours,
            "total_transfers": len(recent),
            "total_volume": round(sum(t.amount for t in recent), 2),
            "inflows": dict(inflows),
            "outflows": dict(outflows),
            "net_flows": net_flows,
            "by_token": dict(by_token),
            "by_bridge": dict(by_bridge),
            "avg_transfer_size": round(sum(t.amount for t in recent) / max(1, len(recent)), 2),
        }

    # === Trends ===

    def get_volume_trend(self, days: int = 7) -> list[dict]:
        """Get daily volume trend."""
        trend = []
        for d in range(days, 0, -1):
            day = (datetime.utcnow() - timedelta(days=d)).date()
            day_start = datetime(day.year, day.month, day.day).isoformat()
            day_end = (datetime(day.year, day.month, day.day) + timedelta(days=1)).isoformat()

            day_transfers = [t for t in self._transfers.values() if day_start <= t.timestamp < day_end]
            volume = sum(t.amount for t in day_transfers)

            by_chain = defaultdict(float)
            for t in day_transfers:
                by_chain[t.source_chain] += t.amount

            trend.append({
                "date": day.isoformat(),
                "transfers": len(day_transfers),
                "volume": round(volume, 2),
                "by_source": dict(by_chain),
            })
        return trend

    def get_token_distribution(self) -> list[dict]:
        """Get token distribution across all transfers."""
        token_stats = defaultdict(lambda: {"count": 0, "volume": 0.0, "chains": set()})
        for t in self._transfers.values():
            token_stats[t.token]["count"] += 1
            token_stats[t.token]["volume"] += t.amount
            token_stats[t.token]["chains"].add(t.source_chain)
            token_stats[t.token]["chains"].add(t.target_chain)

        return [
            {
                "token": token,
                "transfer_count": s["count"],
                "total_volume": round(s["volume"], 2),
                "avg_transfer_size": round(s["volume"] / max(1, s["count"]), 2),
                "chain_count": len(s["chains"]),
                "chains": sorted(list(s["chains"])),
            }
            for token, s in sorted(token_stats.items(), key=lambda x: x[1]["volume"], reverse=True)
        ]

    # === Comparison ===

    def compare_chains(self, chains: list[str] = None) -> list[dict]:
        """Compare metrics across chains."""
        if chains is None:
            chains = [c.value for c in ChainType]

        results = []
        for chain in chains:
            m = self.get_chain_metrics(chain)
            if m:
                results.append({
                    "chain": m.chain,
                    "total_transfers": m.total_transfers,
                    "total_volume": round(m.total_volume, 2),
                    "inbound_volume": round(m.inbound_volume, 2),
                    "outbound_volume": round(m.outbound_volume, 2),
                    "net_flow": round(m.inbound_volume - m.outbound_volume, 2),
                    "active_addresses": m.active_addresses,
                    "avg_transfer_size": round(m.avg_transfer_size, 2),
                    "success_rate": m.success_rate,
                    "avg_duration": round(m.avg_duration, 1),
                })
        return results

    # === Stats ===

    def get_stats(self) -> dict:
        transfers = list(self._transfers.values())
        confirmed = [t for t in transfers if t.status == "confirmed"]
        pending = [t for t in transfers if t.status == "pending"]
        failed = [t for t in transfers if t.status == "failed"]

        return {
            "total_transfers": len(transfers),
            "confirmed": len(confirmed),
            "pending": len(pending),
            "failed": len(failed),
            "success_rate": round(len(confirmed) / max(1, len(transfers)) * 100, 2),
            "total_volume": round(sum(t.amount for t in transfers), 2),
            "avg_transfer_size": round(sum(t.amount for t in transfers) / max(1, len(transfers)), 2),
            "total_chains": len(ChainType),
            "active_corridors": len(self._corridors),
            "bridges_used": len(set(t.bridge_protocol for t in transfers)),
            "tokens_transferred": len(set(t.token for t in transfers)),
            "avg_duration": round(sum(t.duration_seconds for t in confirmed) / max(1, len(confirmed)), 1),
            "total_gas_paid": round(sum(t.gas_paid for t in transfers), 2),
        }

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        return {
            "stats": self.get_stats(),
            "flow_24h": self.get_flow_analysis(24),
            "flow_7d": self.get_flow_analysis(168),
            "volume_trend": self.get_volume_trend(7),
            "chain_comparison": self.compare_chains(),
            "top_corridors": [c.to_dict() for c in self.list_corridors(limit=10)],
            "token_distribution": self.get_token_distribution(),
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 60):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("cross_chain_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Simulate incoming transfers
                import random
                chains = [c.value for c in ChainType]
                tokens = ["VRS", "ETH", "USDC", "USDT"]
                source = random.choice(chains)
                target = random.choice([c for c in chains if c != source])
                self.record_transfer(
                    source_chain=source, target_chain=target,
                    token=random.choice(tokens), amount=round(random.uniform(100, 50000), 2),
                    sender=f"0x{secrets.token_hex(20)}", recipient=f"0x{secrets.token_hex(20)}",
                    status=random.choices(["confirmed", "pending"], weights=[90, 10])[0],
                    duration_seconds=random.randint(2, 120),
                )
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Chains ===

    def list_chains(self) -> list[dict]:
        return [{"value": c.value, "name": c.value.title(), "display": c.value.upper()} for c in ChainType]


_service: Optional[CrossChainAnalyticsService] = None

def get_cross_chain_analytics_service() -> CrossChainAnalyticsService:
    global _service
    if _service is None:
        _service = CrossChainAnalyticsService()
    return _service
