"""
Verdis-Aware Agent Enhancement — Phase 17

Automatically injects Verdis blockchain context into AI agent prompts
and provides Verdis-specific task routing. This ensures every agent
operation has full knowledge of the Verdis ecosystem.

Features:
- Auto-inject Verdis context into agent system prompts
- Verdis-specific task types
- Live chain state injection (block height, validators, peers)
- Project-aware agent routing
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.verdis_agent_enhancer")


# Verdis-specific task types (extending base TaskType)
VERDIS_TASK_TYPES = {
    "consensus_review": "Review BABE/GRANDPA consensus parameters",
    "pallet_audit": "Audit a specific Substrate pallet",
    "supply_invariant_check": "Verify 100B total supply invariant",
    "validator_health_check": "Assess validator network health",
    "dex_safety_review": "Review AmmDex for reentrancy and overflow",
    "eco_feature_audit": "Audit carbon credit / green validator / reforestation pallets",
    "bridge_security_review": "Review cross-chain bridge security",
    "runtime_upgrade_review": "Review runtime version upgrade",
    "tokenomics_validation": "Validate token distribution and vesting",
    "governance_review": "Review on-chain governance configuration",
}


@dataclass
class VerdisAgentContext:
    """Verdis-specific context injected into agent prompts."""
    chain_name: str = "Verdis"
    token_symbol: str = "VRDX"
    ss58_prefix: int = 909
    consensus: str = "DPoS + BABE/GRANDPA"
    total_supply: str = "100,000,000,000 VRS"
    circulating_supply: str = "15,000,000,000 (15% at TGE)"
    validator_count: int = 14
    target_validators: int = 14
    pallets: list = field(default_factory=lambda: [
        "Balances", "AmmDex", "CarbonCredits", "GreenValidator",
        "Reforestation", "FungibleTokens", "NFT", "Governance",
        "Treasury", "Council", "Session", "Staking", "Sudo"
    ])
    spec_version: int = 11
    impl_version: int = 6
    rpc_method_count: int = 121
    domain: str = "verdischain.com"
    node_count: int = 18
    block_time: str = "~6 seconds"
    dex_pools: int = 6
    test_count: int = 133

    def to_prompt(self) -> str:
        """Generate context string for injection into agent prompts."""
        return f"""
=== VERDIS BLOCKCHAIN CONTEXT ===
Chain: {self.chain_name} ({self.token_symbol}, SS58: {self.ss58_prefix})
Consensus: {self.consensus}
Total Supply: {self.total_supply}
Circulating: {self.circulating_supply}
Validators: {self.validator_count}/{self.target_validators}
Pallets ({len(self.pallets)}): {', '.join(self.pallets)}
Spec Version: {self.spec_version}, Impl Version: {self.impl_version}
RPC Methods: {self.rpc_method_count}
Domain: {self.domain}
Nodes: {self.node_count}
Block Time: {self.block_time}
DEX Pools: {self.dex_pools}
Tests: {self.test_count}

ECO FEATURES:
- CarbonCredits: Carbon credit tracking and retirement
- GreenValidator: Green validator scoring (carbon footprint, renewable energy)
- Reforestation: Reforestation logging and verification

TOKENOMICS (8 categories):
- Community 35%, Treasury 20%, Team 15%, Investors 10%
- Staking 10%, Liquidity 5%, Advisors 3%, Airdrop 2%
- Vesting: 60-day (Seed/Private), 30-day (Public/Final)

REVIEW GUIDELINES:
1. Always check consensus safety (BABE/GRANDPA finality)
2. Verify token supply invariants (100B total)
3. Validate DPoS validator rotation logic
4. Check AMM DEX for reentrancy and arithmetic overflow
5. Ensure eco pallets track carbon correctly
6. Verify GRANDPA finality is not disrupted
=== END VERDIS CONTEXT ===
"""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentActivity:
    """Record of an AI agent activity for the activity feed."""
    id: str = field(default_factory=lambda: f"activity-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agent_name: str = ""
    task_type: str = ""
    status: str = "pending"  # pending, running, completed, failed
    project: str = ""
    input_summary: str = ""
    output_summary: str = ""
    score: Optional[float] = None
    verdict: Optional[str] = None
    findings_count: int = 0
    recommendations_count: int = 0
    tokens_used: int = 0
    latency_ms: float = 0.0
    is_simulation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class VerdisAgentEnhancer:
    """
    Enhances AI agents with Verdis-specific context and tracking.
    """

    def __init__(self, max_activities: int = 1000):
        self._context = VerdisAgentContext()
        self._activities: list[AgentActivity] = []
        self._max_activities = max_activities
        self._lock = threading.Lock()
        self._enhancement_enabled = True

    def get_context(self) -> VerdisAgentContext:
        """Get the Verdis agent context."""
        return self._context

    def get_context_prompt(self) -> str:
        """Get the context as a prompt string for injection."""
        return self._context.to_prompt() if self._enhancement_enabled else ""

    def update_context(self, **kwargs):
        """Update Verdis context (e.g., after health check)."""
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)
        logger.info("verdis_agent_context_updated", fields=list(kwargs.keys()))

    def enhance_prompt(self, system_prompt: str, project: str = None) -> str:
        """
        Enhance an agent's system prompt with Verdis context.
        Only injects if the project is Verdis or no project specified.
        """
        if not self._enhancement_enabled:
            return system_prompt
        if project and project.lower() not in ("verdis", "verdis blockchain", ""):
            return system_prompt
        return system_prompt + "\n\n" + self.get_context_prompt()

    def record_activity(self, activity: AgentActivity):
        """Record an agent activity."""
        with self._lock:
            self._activities.append(activity)
            if len(self._activities) > self._max_activities:
                self._activities.pop(0)

    def get_activities(self, agent_name: str = None, limit: int = 50) -> list[AgentActivity]:
        """Get agent activities, optionally filtered by agent."""
        activities = self._activities
        if agent_name:
            activities = [a for a in activities if a.agent_name == agent_name]
        return list(reversed(activities))[:limit]

    def get_agent_stats(self) -> list[dict]:
        """Get per-agent statistics."""
        agent_stats: dict[str, dict] = {}
        for activity in self._activities:
            name = activity.agent_name
            if name not in agent_stats:
                agent_stats[name] = {
                    "agent_name": name,
                    "total_tasks": 0,
                    "completed": 0,
                    "failed": 0,
                    "avg_score": 0.0,
                    "total_tokens": 0,
                    "avg_latency_ms": 0.0,
                    "go_verdicts": 0,
                    "nogo_verdicts": 0,
                    "simulations": 0,
                }
            stats = agent_stats[name]
            stats["total_tasks"] += 1
            if activity.status == "completed":
                stats["completed"] += 1
            elif activity.status == "failed":
                stats["failed"] += 1
            if activity.score:
                stats["avg_score"] = (stats["avg_score"] * (stats["completed"] - 1) + activity.score) / max(stats["completed"], 1)
            if activity.verdict == "GO":
                stats["go_verdicts"] += 1
            elif activity.verdict == "NO-GO":
                stats["nogo_verdicts"] += 1
            if activity.is_simulation:
                stats["simulations"] += 1
            stats["total_tokens"] += activity.tokens_used
            stats["avg_latency_ms"] = (stats["avg_latency_ms"] * (stats["total_tasks"] - 1) + activity.latency_ms) / stats["total_tasks"]

        return list(agent_stats.values())

    def get_overview(self) -> dict:
        """Get overview of all agent activities."""
        stats = self.get_agent_stats()
        return {
            "total_activities": len(self._activities),
            "total_agents": len(stats),
            "agent_stats": stats,
            "context": self._context.to_dict(),
            "enhancement_enabled": self._enhancement_enabled,
            "verdis_task_types": VERDIS_TASK_TYPES,
        }

    def enable(self):
        self._enhancement_enabled = True
        logger.info("verdis_agent_enhancement_enabled")

    def disable(self):
        self._enhancement_enabled = False
        logger.info("verdis_agent_enhancement_disabled")


# Singleton
_enhancer: Optional[VerdisAgentEnhancer] = None


def get_verdis_enhancer() -> VerdisAgentEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = VerdisAgentEnhancer()
    return _enhancer
