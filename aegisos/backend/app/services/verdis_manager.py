"""
Verdis Project Manager — Phase 16

Makes EvolvixOS actively manage the Verdis blockchain as its first project.
This is the production integration layer that:
- Registers Verdis as a managed project
- Sets up automated monitoring pipelines
- Configures AI agents with Verdis context
- Tracks Verdis ecosystem health over time
- Manages Verdis-specific pipeline templates
- Provides Verdis context to all AI agents
"""

from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
from app.core.logging import get_logger
from app.integrations.verdis import VerdisIntegration

logger = get_logger("service.verdis_manager")


@dataclass
class VerdisHealthSnapshot:
    """A point-in-time snapshot of Verdis blockchain health."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    connected: bool = False
    block_height: str = "0"
    peers: int = 0
    is_syncing: bool = False
    spec_version: int = 0
    impl_version: int = 0
    validator_count: int = 0
    rpc_method_count: int = 0
    total_issuance: Optional[str] = None
    node_name: str = ""
    node_version: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerdisAlert:
    """An alert from the Verdis monitoring system."""
    id: str = field(default_factory=lambda: f"alert-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    severity: str = "info"  # info, warning, critical
    category: str = ""  # connectivity, consensus, validators, performance, security
    message: str = ""
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VerdisEcosystemComponent:
    """A component of the Verdis ecosystem tracked by EvolvixOS."""
    name: str = ""
    type: str = ""  # blockchain, sdk, cli, bridge, explorer, wallet, docs
    status: str = "unknown"  # healthy, degraded, offline, unknown
    version: str = ""
    last_checked: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    url: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# Verdis ecosystem components
VERDIS_COMPONENTS = [
    VerdisEcosystemComponent(
        name="Verdis Chain (Core)", type="blockchain",
        url="https://verdischain.com/rpc", version="spec v11, impl v6",
        notes="DPoS + BABE/GRANDPA, 14 validators, 13 pallets"
    ),
    VerdisEcosystemComponent(
        name="TypeScript SDK", type="sdk",
        url="https://github.com/Protremix/Verdischain-", version="1.0.0",
        notes="19 files, 13 tests, @polkadot/api wrapper"
    ),
    VerdisEcosystemComponent(
        name="CLI Tool", type="cli",
        url="https://github.com/Protremix/Verdischain-", version="1.0.0",
        notes="13 files, 6 commands"
    ),
    VerdisEcosystemComponent(
        name="Bridge (Solidity + Relayer)", type="bridge",
        url="https://github.com/Protremix/Verdischain-", version="0.1.0",
        notes="Multi-relayer M-of-N, EIP-712, not yet deployed"
    ),
    VerdisEcosystemComponent(
        name="Verdiscan Explorer", type="explorer",
        url="https://verdischain.com", version="1.0.0",
        notes="Dark-themed Solscan-style, 11 subdomains"
    ),
    VerdisEcosystemComponent(
        name="Android Wallet", type="wallet",
        url="https://github.com/Protremix/Verdischain-", version="1.0.0",
        notes="Native, dependency-free widgets"
    ),
    VerdisEcosystemComponent(
        name="Documentation", type="docs",
        url="https://github.com/Protremix/Verdischain-", version="1.0.0",
        notes="4 files, 4096 words, English consolidated"
    ),
]

# Verdis-specific pipeline template
VERDIS_PIPELINE_TEMPLATE = {
    "name": "Verdis Blockchain Audit",
    "description": "Comprehensive audit of Verdis blockchain components",
    "category": "security",
    "icon": "🌱",
    "default_priority": "high",
    "default_project_type": "blockchain",
    "default_constraints": [
        "Must pass all 133 workspace tests",
        "Must build native AND WASM",
        "Must pass cargo fmt --check",
        "Must pass cargo clippy",
        "Must maintain 14 validators",
        "Must preserve 100B total supply",
    ],
    "default_acceptance_criteria": [
        "All tests pass (133+)",
        "Native build succeeds",
        "WASM build succeeds",
        "No new clippy warnings",
        "Code formatted correctly",
        "Chain produces blocks at ~6s intervals",
        "GRANDPA finality working",
    ],
    "skip_stages": [],
    "stage_overrides": {
        "security": {"max_retries": 3, "agent": "security"},
        "performance": {"max_retries": 2, "agent": "cto"},
        "review": {"max_retries": 1, "agent": "cto"},
    },
    "estimated_duration_hours": 8.0,
    "complexity": "high",
    "tags": ["blockchain", "rust", "substrate", "verdis", "audit"],
}

# AI agent context for Verdis
VERDIS_AGENT_CONTEXT = """
You are working on the Verdis blockchain — the world's first fully green, carbon-negative blockchain ecosystem.

Key facts:
- Rust + Substrate core, DPoS consensus with BABE/GRANDPA
- 14 validators live on verdischain.com
- Spec v11, impl v6, 133 tests passing
- 13 pallets: Balances, AmmDex, CarbonCredits, GreenValidator, Reforestation, FungibleTokens, NFT, Governance, Treasury, Council, Session, Staking, Sudo
- 121 RPC methods, GRANDPA finality working
- 100B total supply (VRS/VRDX), 15B circulating at TGE
- 6 DEX liquidity pools at genesis
- TypeScript SDK, CLI, Bridge (not yet deployed)
- Verdiscan explorer (dark Solscan-style)
- Native Android wallet (dependency-free)
- Domain: verdischain.com (18 nodes, systemd-deployed)
- GPT-4o is the permanent CTO/architect/reviewer

Eco features:
- Carbon credit tracking (CarbonCredits pallet)
- Green validator scoring (GreenValidator pallet)
- Reforestation logging (Reforestation pallet)
- Carbon-negative blockchain design

Tokenomics (8 categories):
- Community 35%, Treasury 20%, Team 15%, Investors 10%
- Staking 10%, Liquidity 5%, Advisors 3%, Airdrop 2%
- 60-day vesting (Seed/Private), 30-day (Public/Final)

When reviewing Verdis code:
1. Always check consensus safety (BABE/GRANDPA)
2. Verify token supply invariants (100B total)
3. Validate DPoS validator logic
4. Check AMM DEX for reentrancy/overflow
5. Ensure eco pallets track carbon correctly
6. Verify GRANDPA finality is not disrupted
"""


class VerdisProjectManager:
    """Manages the Verdis blockchain as an EvolvixOS managed project."""

    def __init__(self, max_snapshots: int = 1440, max_alerts: int = 500):
        self._integration = VerdisIntegration()
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._alerts: list[VerdisAlert] = []
        self._components: dict[str, VerdisEcosystemComponent] = {
            c.name: c for c in VERDIS_COMPONENTS
        }
        self._max_alerts = max_alerts
        self._lock = threading.Lock()
        self._last_check: Optional[str] = None
        self._monitoring_enabled = True
        self._project_registered = False

    def register_project(self) -> dict:
        """Register Verdis as a managed project in EvolvixOS."""
        if self._project_registered:
            return {"status": "already_registered", "project": "Verdis"}

        self._project_registered = True
        logger.info("verdis_project_registered")

        return {
            "status": "registered",
            "project": {
                "name": "Verdis Blockchain",
                "type": "blockchain",
                "domain": "verdischain.com",
                "description": "World's first fully green, carbon-negative blockchain ecosystem",
                "tech_stack": ["Rust", "Substrate", "BABE/GRANDPA", "DPoS"],
                "components": list(self._components.keys()),
                "pipeline_template": VERDIS_PIPELINE_TEMPLATE["name"],
                "agent_context": "Loaded (Verdis-specific AI context)",
            },
            "pipeline_template": VERDIS_PIPELINE_TEMPLATE,
            "agent_context_loaded": True,
        }

    def run_health_check(self) -> VerdisHealthSnapshot:
        """Run a health check on the Verdis blockchain and store the snapshot."""
        snapshot = VerdisHealthSnapshot()

        try:
            health = self._integration.get_chain_health()
            snapshot.connected = health.get("connected", False)
            snapshot.block_height = health.get("block_height", "0")
            snapshot.peers = health.get("peers", 0)
            snapshot.is_syncing = health.get("is_syncing", False)
            snapshot.spec_version = health.get("spec_version", 0)
            snapshot.impl_version = health.get("impl_version", 0)

            validators = self._integration.get_validators()
            snapshot.validator_count = len(validators)

            network = self._integration.get_network_info()
            snapshot.node_name = network.get("node_name", "")
            snapshot.node_version = network.get("node_version", "")
            snapshot.rpc_method_count = network.get("rpc_method_count", 0)

        except Exception as e:
            logger.error("verdis_health_check_failed", error=str(e))
            snapshot.connected = False

        with self._lock:
            self._snapshots.append(snapshot)
            self._last_check = snapshot.timestamp

        # Generate alerts based on health
        self._check_for_alerts(snapshot)

        return snapshot

    def _check_for_alerts(self, snapshot: VerdisHealthSnapshot):
        """Generate alerts based on health snapshot."""
        if not snapshot.connected:
            self._create_alert("critical", "connectivity",
                              "Verdis blockchain is not reachable at verdischain.com/rpc")
        elif snapshot.peers < 5:
            self._create_alert("warning", "connectivity",
                              f"Low peer count: {snapshot.peers} peers")
        
        if snapshot.is_syncing:
            self._create_alert("info", "consensus",
                              "Verdis node is currently syncing")
        
        if snapshot.validator_count > 0 and snapshot.validator_count < 10:
            self._create_alert("warning", "validators",
                              f"Low validator count: {snapshot.validator_count} (expected 14)")
        
        if snapshot.spec_version > 0 and snapshot.spec_version < 11:
            self._create_alert("warning", "consensus",
                              f"Outdated spec version: {snapshot.spec_version} (expected 11)")

    def _create_alert(self, severity: str, category: str, message: str):
        """Create an alert if the same alert does not already exist unresolved."""
        # Check for duplicate
        for alert in self._alerts:
            if not alert.resolved and alert.category == category and alert.message == message:
                return  # Don't duplicate

        alert = VerdisAlert(severity=severity, category=category, message=message)
        with self._lock:
            self._alerts.append(alert)
            if len(self._alerts) > self._max_alerts:
                self._alerts.pop(0)
        logger.info("verdis_alert_created", severity=severity, category=category, message=message)

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow().isoformat()
                return True
        return False

    def get_alerts(self, resolved: bool = False, limit: int = 50) -> list[VerdisAlert]:
        """Get alerts."""
        alerts = [a for a in reversed(self._alerts) if a.resolved == resolved]
        return alerts[:limit]

    def get_snapshots(self, limit: int = 100) -> list[VerdisHealthSnapshot]:
        """Get health history."""
        return list(reversed(self._snapshots))[:limit]

    def get_latest_snapshot(self) -> Optional[VerdisHealthSnapshot]:
        """Get the most recent health snapshot."""
        if self._snapshots:
            return self._snapshots[-1]
        return None

    def get_components(self) -> list[VerdisEcosystemComponent]:
        """Get all tracked Verdis ecosystem components."""
        return list(self._components.values())

    def update_component_status(self, name: str, status: str, notes: str = ""):
        """Update a component status."""
        if name in self._components:
            comp = self._components[name]
            comp.status = status
            comp.last_checked = datetime.utcnow().isoformat()
            if notes:
                comp.notes = notes
            logger.info("verdis_component_updated", name=name, status=status)

    def get_project_overview(self) -> dict:
        """Get complete Verdis project overview for dashboard."""
        latest = self.get_latest_snapshot()
        alerts = self.get_alerts(resolved=False)

        return {
            "project_name": "Verdis Blockchain",
            "project_type": "blockchain",
            "domain": "verdischain.com",
            "registered": self._project_registered,
            "monitoring_enabled": self._monitoring_enabled,
            "last_check": self._last_check,
            "health": latest.to_dict() if latest else None,
            "components": [c.to_dict() for c in self._components.values()],
            "active_alerts": len(alerts),
            "total_alerts": len(self._alerts),
            "snapshot_count": len(self._snapshots),
            "pipeline_template": VERDIS_PIPELINE_TEMPLATE,
            "agent_context": VERDIS_AGENT_CONTEXT[:200] + "...",
        }

    def get_agent_context(self) -> str:
        """Get Verdis-specific context for AI agents."""
        return VERDIS_AGENT_CONTEXT

    def get_health_summary(self) -> str:
        """Get human-readable health summary."""
        try:
            return self._integration.get_health_summary()
        except Exception:
            return "Verdis blockchain RPC not reachable. Last known state: spec v11, 14 validators, 133 tests."

    def enable_monitoring(self):
        self._monitoring_enabled = True
        logger.info("verdis_monitoring_enabled")

    def disable_monitoring(self):
        self._monitoring_enabled = False
        logger.info("verdis_monitoring_disabled")

    def get_stats(self) -> dict:
        """Get monitoring statistics."""
        return {
            "registered": self._project_registered,
            "monitoring_enabled": self._monitoring_enabled,
            "total_snapshots": len(self._snapshots),
            "total_alerts": len(self._alerts),
            "active_alerts": sum(1 for a in self._alerts if not a.resolved),
            "resolved_alerts": sum(1 for a in self._alerts if a.resolved),
            "components_tracked": len(self._components),
            "last_check": self._last_check,
        }


# Singleton
_manager: Optional[VerdisProjectManager] = None


def get_verdis_manager() -> VerdisProjectManager:
    global _manager
    if _manager is None:
        _manager = VerdisProjectManager()
    return _manager
