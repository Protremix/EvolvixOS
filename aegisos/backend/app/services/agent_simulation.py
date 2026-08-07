"""
Agent Simulation Framework — Phase 17

Provides mock data and realistic scenarios for testing AI agents
without requiring real OpenAI API calls. This enables:
- Running pipelines in test/simulation mode
- Demonstrating agent capabilities without API costs
- CI/CD testing of agent workflows
- Training scenarios for new users
"""

from typing import Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import deque
import threading
from app.core.logging import get_logger

logger = get_logger("service.agent_simulation")


@dataclass
class SimulationScenario:
    """A pre-defined scenario for agent simulation."""
    id: str = ""
    name: str = ""
    description: str = ""
    agent_name: str = ""
    task_type: str = ""
    mock_input: dict = field(default_factory=dict)
    mock_output: dict = field(default_factory=dict)
    mock_score: float = 8.0
    mock_verdict: str = "GO"
    mock_findings: list = field(default_factory=list)
    mock_recommendations: list = field(default_factory=list)
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# Pre-built scenarios covering real-world Verdis/EvolvixOS situations
BUILTIN_SCENARIOS = [
    SimulationScenario(
        id="sim-001",
        name="Verdis Runtime Upgrade Review",
        description="CTO agent reviews a runtime upgrade from spec v11 to v12",
        agent_name="cto_agent",
        task_type="architecture_review",
        mock_input={
            "feature": "Runtime upgrade to spec v12",
            "changes": ["New pallet: SmartContracts", "Updated AmmDex weights", "Session config change"],
            "risk_level": "medium",
        },
        mock_output={
            "summary": "Runtime upgrade from spec v11 to v12 is architecturally sound. New SmartContracts pallet adds EVM compatibility without disrupting existing pallets. Weight updates for AmmDex are appropriate for current usage patterns.",
            "scores": {
                "scalability": 9.0,
                "security": 8.5,
                "maintainability": 8.0,
                "performance": 8.5,
                "developer_experience": 9.0,
            },
        },
        mock_score=8.6,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "Medium", "description": "SmartContracts pallet should include gas metering audit before mainnet"},
            {"severity": "Low", "description": "Consider adding migration tests for AmmDex weight changes"},
        ],
        mock_recommendations=[
            "Run benchmark suite with new weights before deployment",
            "Add integration tests for SmartContracts ↔ FungibleTokens interaction",
            "Update documentation with new RPC methods",
        ],
        tags=["blockchain", "runtime", "upgrade"],
    ),
    SimulationScenario(
        id="sim-002",
        name="Bridge Security Audit",
        description="Security agent audits the Verdis-Ethereum bridge contract",
        agent_name="security_agent",
        task_type="security_review",
        mock_input={
            "component": "VerdisBridge.sol",
            "lines": 450,
            "features": ["Multi-relayer M-of-N", "EIP-712 signatures", "Fee mechanism", "Pausable"],
        },
        mock_output={
            "summary": "Bridge contract implements proper multi-relayer consensus with M-of-N threshold. EIP-712 signature verification is correctly implemented. ReentrancyGuard and Pausable provide additional safety layers.",
        },
        mock_score=8.0,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "High", "description": "Relayer set should be updatable via governance, not just admin"},
            {"severity": "Medium", "description": "Fee mechanism lacks configurable rate cap"},
            {"severity": "Low", "description": "Missing events for fee collection"},
        ],
        mock_recommendations=[
            "Move relayer management to Governance pallet",
            "Add fee rate cap with maximum change per update",
            "Emit BridgeFeeCollected event",
            "Add comprehensive bridge integration tests",
        ],
        tags=["bridge", "security", "solidity"],
    ),
    SimulationScenario(
        id="sim-003",
        name="AMM DEX Performance Analysis",
        description="CTO agent analyzes AmmDex pallet performance under load",
        agent_name="cto_agent",
        task_type="architecture_review",
        mock_input={
            "component": "AmmDex pallet",
            "current_tps": 150,
            "target_tps": 1000,
            "pools": 6,
        },
        mock_output={
            "summary": "AmmDex currently handles 150 TPS. To reach 1000 TPS, recommend optimizing pool reservation logic and implementing batch swaps. Current constant-product AMM is correct but can be optimized with SIMD instructions.",
        },
        mock_score=7.5,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "High", "description": "Pool reservation uses sequential lock acquisition — risk of contention under high TPS"},
            {"severity": "Medium", "description": "No batch swap support — each swap is a separate transaction"},
            {"severity": "Low", "description": "Price oracle update frequency could be configurable"},
        ],
        mock_recommendations=[
            "Implement parallel pool locking with fine-grained per-pool locks",
            "Add batch swap dispatchable for multi-hop swaps in single transaction",
            "Make oracle update frequency configurable per pool",
            "Add TPS benchmark to CI pipeline",
        ],
        tags=["amm", "dex", "performance"],
    ),
    SimulationScenario(
        id="sim-004",
        name="Carbon Credit Pallet Test Review",
        description="QA agent reviews test coverage for CarbonCredits pallet",
        agent_name="qa_agent",
        task_type="quality_gate",
        mock_input={
            "pallet": "CarbonCredits",
            "test_count": 18,
            "coverage": 87,
            "missing": ["edge case: zero carbon credits", "edge case: overflow on retirement"],
        },
        mock_output={
            "summary": "CarbonCredits pallet has 87% test coverage with 18 tests. Two critical edge cases are missing: zero-credit handling and overflow on retirement. Recommend adding these before production.",
        },
        mock_score=7.0,
        mock_verdict="NO-GO",
        mock_findings=[
            {"severity": "High", "description": "Missing test: zero carbon credit transfer"},
            {"severity": "High", "description": "Missing test: overflow on credit retirement"},
            {"severity": "Medium", "description": "No benchmark tests for credit issuance"},
        ],
        mock_recommendations=[
            "Add test_credits_zero_transfer()",
            "Add test_credits_retire_overflow()",
            "Add benchmark for credit issuance throughput",
            "Increase coverage to 95% before mainnet",
        ],
        tags=["carbon", "qa", "testing"],
    ),
    SimulationScenario(
        id="sim-005",
        name="Green Validator Scoring Review",
        description="Architect agent reviews the GreenValidator pallet design",
        agent_name="architect_agent",
        task_type="system_design",
        mock_input={
            "pallet": "GreenValidator",
            "features": ["Carbon footprint tracking", "Green score calculation", "Validator ranking"],
        },
        mock_output={
            "summary": "GreenValidator pallet design is solid. Carbon footprint tracking uses a verifiable oracle model. Green score calculation uses a transparent multi-factor formula. Validator ranking updates per session.",
        },
        mock_score=8.5,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "Medium", "description": "Oracle data source should be diversified to prevent manipulation"},
            {"severity": "Low", "description": "Green score formula weights should be governance-configurable"},
        ],
        mock_recommendations=[
            "Add multiple oracle sources for carbon footprint data",
            "Make green score weights configurable via governance",
            "Add green score history tracking for trend analysis",
            "Document the scoring formula in the whitepaper",
        ],
        tags=["green", "validator", "architecture"],
    ),
    SimulationScenario(
        id="sim-006",
        name="Pipeline: New Feature (Token Transfer)",
        description="Full pipeline simulation for implementing token transfer feature",
        agent_name="planner_agent",
        task_type="task_decomposition",
        mock_input={
            "feature": "Token transfer with vesting support",
            "project": "Verdis",
            "complexity": "medium",
        },
        mock_output={
            "summary": "Token transfer with vesting decomposed into 5 tasks: 1) Update Balances pallet with vesting logic, 2) Add transfer_with_vesting dispatchable, 3) Implement vesting schedule storage, 4) Add tests for vesting scenarios, 5) Update SDK with vesting API",
        },
        mock_score=8.0,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "Low", "description": "Vesting schedule should support cliff and linear unlock"},
        ],
        mock_recommendations=[
            "Implement vesting as separate pallet for modularity",
            "Add SDK method: transferWithVesting()",
            "Include vesting in CLI commands",
            "Update Verdiscan to show vesting schedules",
        ],
        tags=["pipeline", "feature", "planning"],
    ),
    SimulationScenario(
        id="sim-007",
        name="CI Failure Diagnosis",
        description="CI Healer diagnoses a failed CI run",
        agent_name="ci_healer_agent",
        task_type="ci_heal",
        mock_input={
            "failure": "cargo test --release --workspace failed",
            "error": "panicked at 'assertion failed: total_supply == 100_000_000_000'",
            "file": "pallets/balances/src/tests.rs",
        },
        mock_output={
            "summary": "CI failure caused by supply invariant assertion. The test expects 100B total supply but actual supply is 100B + 1000 (genesis allocation added twice). Fix: remove duplicate genesis allocation in chain_spec.rs.",
        },
        mock_score=9.0,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "High", "description": "Duplicate genesis allocation in chain_spec.rs"},
        ],
        mock_recommendations=[
            "Remove duplicate allocation line in chain_spec.rs",
            "Add test_total_supply_invariant() to verify 100B after genesis",
            "Add CI check for supply invariant on every PR",
        ],
        tags=["ci", "healer", "fix"],
    ),
    SimulationScenario(
        id="sim-008",
        name="Documentation Generation for SDK",
        description="Documentation agent generates API docs for TypeScript SDK",
        agent_name="documentation_agent",
        task_type="doc_generation",
        mock_input={
            "component": "TypeScript SDK",
            "files": 19,
            "methods": ["transfer", "getBalance", "subscribe", "getValidators", "submitExtrinsic"],
        },
        mock_output={
            "summary": "Generated comprehensive API documentation for TypeScript SDK covering all 19 files and 5 primary methods. Documentation includes installation guide, quick start, API reference, and code examples.",
        },
        mock_score=8.5,
        mock_verdict="GO",
        mock_findings=[
            {"severity": "Low", "description": "Add TypeScript types documentation"},
            {"severity": "Info", "description": "Consider adding interactive examples"},
        ],
        mock_recommendations=[
            "Publish docs to GitHub Pages",
            "Add JSDoc comments to all public methods",
            "Create interactive playground",
        ],
        tags=["docs", "sdk", "typescript"],
    ),
]


class AgentSimulationService:
    """Manages agent simulation scenarios and execution."""

    def __init__(self, max_history: int = 500):
        self._scenarios: dict[str, SimulationScenario] = {
            s.id: s for s in BUILTIN_SCENARIOS
        }
        self._custom_scenarios: dict[str, SimulationScenario] = {}
        self._execution_history: deque = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def list_scenarios(self, agent_name: str = None, tag: str = None) -> list[SimulationScenario]:
        """List all scenarios, optionally filtered."""
        all_scenarios = list(self._scenarios.values()) + list(self._custom_scenarios.values())
        if agent_name:
            all_scenarios = [s for s in all_scenarios if s.agent_name == agent_name]
        if tag:
            all_scenarios = [s for s in all_scenarios if tag in s.tags]
        return all_scenarios

    def get_scenario(self, scenario_id: str) -> Optional[SimulationScenario]:
        """Get a specific scenario."""
        return self._scenarios.get(scenario_id) or self._custom_scenarios.get(scenario_id)

    def create_scenario(self, scenario: SimulationScenario) -> SimulationScenario:
        """Create a custom scenario."""
        if not scenario.id:
            scenario.id = f"custom-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        self._custom_scenarios[scenario.id] = scenario
        logger.info("simulation_scenario_created", id=scenario.id, name=scenario.name)
        return scenario

    def run_simulation(self, scenario_id: str) -> dict:
        """Run a simulation scenario and return mock agent output."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": "Scenario not found", "scenario_id": scenario_id}

        result = {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "agent_name": scenario.agent_name,
            "task_type": scenario.task_type,
            "input": scenario.mock_input,
            "output": scenario.mock_output,
            "score": scenario.mock_score,
            "verdict": scenario.mock_verdict,
            "findings": scenario.mock_findings,
            "recommendations": scenario.mock_recommendations,
            "simulated_at": datetime.utcnow().isoformat(),
            "is_simulation": True,
        }

        with self._lock:
            self._execution_history.append(result)

        logger.info("simulation_executed", scenario=scenario.name, agent=scenario.agent_name)
        return result

    def run_agent_simulation(self, agent_name: str, task_type: str, data: dict) -> dict:
        """Find best matching scenario for an agent+task and run it."""
        matching = [
            s for s in self.list_scenarios()
            if s.agent_name == agent_name and s.task_type == task_type
        ]
        if not matching:
            # Generic fallback
            return {
                "agent_name": agent_name,
                "task_type": task_type,
                "output": {"summary": f"Simulated {task_type} for {agent_name}"},
                "score": 8.0,
                "verdict": "GO",
                "findings": [],
                "recommendations": ["This is a simulated result"],
                "simulated_at": datetime.utcnow().isoformat(),
                "is_simulation": True,
            }

        # Use first matching scenario
        scenario = matching[0]
        return self.run_simulation(scenario.id)

    def get_history(self, limit: int = 50) -> list[dict]:
        """Get simulation execution history."""
        return list(reversed(self._execution_history))[:limit]

    def get_stats(self) -> dict:
        """Get simulation statistics."""
        return {
            "total_scenarios": len(self._scenarios) + len(self._custom_scenarios),
            "builtin_scenarios": len(self._scenarios),
            "custom_scenarios": len(self._custom_scenarios),
            "total_executions": len(self._execution_history),
            "agents_covered": list(set(s.agent_name for s in self.list_scenarios())),
            "tags": list(set(tag for s in self.list_scenarios() for tag in s.tags)),
        }


# Singleton
_service: Optional[AgentSimulationService] = None


def get_simulation_service() -> AgentSimulationService:
    global _service
    if _service is None:
        _service = AgentSimulationService()
    return _service
