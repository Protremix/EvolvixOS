"""
Tokenomics Dashboard — Phase 36

Token supply tracking, distribution breakdown, vesting schedules,
circulating supply, token utility metrics, and flow analytics.
"""

import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import threading
from app.core.logging import get_logger

logger = get_logger("service.tokenomics")


class AllocationType(str, Enum):
    TOTAL = "total"
    INVESTORS = "investors"
    TEAM = "team"
    TREASURY = "treasury"
    COMMUNITY = "community"
    VALIDATORS = "validators"
    ECOSYSTEM = "ecosystem"
    LIQUIDITY = "liquidity"


class VestingStatus(str, Enum):
    LOCKED = "locked"
    VESTING = "vesting"
    VESTED = "vested"
    CLIFFED = "cliffed"


class FlowType(str, Enum):
    TRANSFER = "transfer"
    MINT = "mint"
    BURN = "burn"
    STAKE = "stake"
    UNSTAKE = "unstake"
    REWARD = "reward"
    GOVERNANCE = "governance"
    TREASURY_SPEND = "treasury_spend"


@dataclass
class TokenAllocation:
    type: str
    total_amount: float
    released: float
    locked: float
    description: str
    percentage: float = 0.0
    vesting_months: int = 0
    cliff_months: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class VestingSchedule:
    id: str
    beneficiary: str
    allocation_type: str
    total_amount: float
    released: float
    cliff_end: str
    vesting_end: str
    monthly_release: float
    status: str = VestingStatus.LOCKED.value
    start_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_release: str = ""
    releases: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TokenFlow:
    id: str
    flow_type: str
    from_addr: str
    to_addr: str
    amount: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    block_height: int = 0
    tx_hash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TokenUtility:
    staked_amount: float = 0
    governance_locked: float = 0
    treasury_balance: float = 0
    liquidity_pools: float = 0
    burned: float = 0
    transaction_fees: float = 0

    def to_dict(self) -> dict:
        return asdict(self)


class TokenomicsService:
    """Token economics tracking and analytics."""

    def __init__(self):
        self._total_supply = 100_000_000_000  # 100B VRS
        self._investor_allocation = 12_000_000_000  # 12B VRS
        self._lock = threading.Lock()
        self._allocations: dict[str, TokenAllocation] = {}
        self._vesting_schedules: dict[str, VestingSchedule] = {}
        self._flows: list[TokenFlow] = []
        self._utility = TokenUtility()
        self._init_default_allocations()

    def _init_default_allocations(self):
        """Initialize default token allocations per Verdis tokenomics."""
        defaults = [
            (AllocationType.INVESTORS.value, 12_000_000_000, "Investor allocation (12B VRS)", 48, 12),
            (AllocationType.TEAM.value, 15_000_000_000, "Team & advisors", 48, 12),
            (AllocationType.TREASURY.value, 20_000_000_000, "Treasury & governance", 0, 0),
            (AllocationType.COMMUNITY.value, 25_000_000_000, "Community rewards & airdrops", 0, 0),
            (AllocationType.VALIDATORS.value, 13_000_000_000, "Validator staking rewards", 0, 0),
            (AllocationType.ECOSYSTEM.value, 10_000_000_000, "Ecosystem development", 24, 6),
            (AllocationType.LIQUIDITY.value, 5_000_000_000, "DEX & market liquidity", 0, 0),
        ]

        for alloc_type, amount, desc, vest_months, cliff_months in defaults:
            released = amount * 0.1  # 10% initial release for vested categories
            if vest_months == 0:
                released = amount  # Fully unlocked
            locked = amount - released
            self._allocations[alloc_type] = TokenAllocation(
                type=alloc_type, total_amount=amount, released=released,
                locked=locked, description=desc,
                percentage=round((amount / self._total_supply) * 100, 2),
                vesting_months=vest_months, cliff_months=cliff_months,
            )

    # === Supply ===

    def get_total_supply(self) -> float:
        return self._total_supply

    def get_circulating_supply(self) -> dict:
        """Calculate circulating supply (released tokens minus locked)."""
        total_released = sum(a.released for a in self._allocations.values())
        total_locked = sum(a.locked for a in self._allocations.values())
        burned = self._utility.burned
        circulating = total_released - burned

        return {
            "total_supply": self._total_supply,
            "circulating": circulating,
            "locked": total_locked,
            "burned": burned,
            "circulating_pct": round((circulating / self._total_supply) * 100, 2),
            "locked_pct": round((total_locked / self._total_supply) * 100, 2),
        }

    # === Allocations ===

    def get_allocations(self) -> list[TokenAllocation]:
        return list(self._allocations.values())

    def get_allocation(self, alloc_type: str) -> Optional[TokenAllocation]:
        return self._allocations.get(alloc_type)

    def update_allocation(self, alloc_type: str, released: float = None, locked: float = None) -> Optional[TokenAllocation]:
        alloc = self._allocations.get(alloc_type)
        if not alloc:
            return None
        if released is not None:
            alloc.released = released
        if locked is not None:
            alloc.locked = locked
        return alloc

    # === Vesting ===

    def create_vesting_schedule(
        self, beneficiary: str, allocation_type: str, total_amount: float,
        vesting_months: int, cliff_months: int = 0,
    ) -> VestingSchedule:
        """Create a vesting schedule for a beneficiary."""
        schedule_id = f"vest-{secrets.token_hex(8)}"
        now = datetime.utcnow()
        cliff_end = now + timedelta(days=cliff_months * 30)
        vesting_end = now + timedelta(days=vesting_months * 30)
        monthly_release = total_amount / max(1, vesting_months - cliff_months) if vesting_months > cliff_months else total_amount

        schedule = VestingSchedule(
            id=schedule_id, beneficiary=beneficiary, allocation_type=allocation_type,
            total_amount=total_amount, released=0,
            cliff_end=cliff_end.isoformat(), vesting_end=vesting_end.isoformat(),
            monthly_release=monthly_release,
        )
        self._vesting_schedules[schedule_id] = schedule
        logger.info("vesting_created", id=schedule_id, beneficiary=beneficiary, amount=total_amount)
        return schedule

    def get_vesting_schedule(self, schedule_id: str) -> Optional[VestingSchedule]:
        return self._vesting_schedules.get(schedule_id)

    def list_vesting_schedules(
        self, beneficiary: str = None, status: str = None,
    ) -> list[VestingSchedule]:
        schedules = list(self._vesting_schedules.values())
        if beneficiary:
            schedules = [s for s in schedules if s.beneficiary == beneficiary]
        if status:
            schedules = [s for s in schedules if s.status == status]
        return schedules

    def release_vested(self, schedule_id: str) -> Optional[VestingSchedule]:
        """Release vested tokens for a schedule."""
        schedule = self._vesting_schedules.get(schedule_id)
        if not schedule:
            return None

        now = datetime.utcnow()
        cliff = datetime.fromisoformat(schedule.cliff_end.replace("Z", ""))
        vest_end = datetime.fromisoformat(schedule.vesting_end.replace("Z", ""))

        if now < cliff:
            schedule.status = VestingStatus.CLIFFED.value
            return schedule

        if now >= vest_end:
            schedule.released = schedule.total_amount
            schedule.status = VestingStatus.VESTED.value
        else:
            # Calculate proportional release
            total_duration = (vest_end - cliff).total_seconds()
            elapsed = (now - cliff).total_seconds()
            vested_amount = (schedule.total_amount * elapsed) / total_duration
            schedule.released = round(vested_amount, 2)
            schedule.status = VestingStatus.VESTING.value

        schedule.last_release = now.isoformat()
        schedule.releases.append({
            "timestamp": now.isoformat(),
            "amount": schedule.released,
            "status": schedule.status,
        })

        return schedule

    def get_vesting_stats(self) -> dict:
        schedules = list(self._vesting_schedules.values())
        return {
            "total_schedules": len(schedules),
            "total_vested": sum(s.total_amount for s in schedules),
            "total_released": sum(s.released for s in schedules),
            "total_locked": sum(s.total_amount - s.released for s in schedules),
            "by_status": {st: sum(1 for s in schedules if s.status == st) for st in set(s.status for s in schedules)},
        }

    # === Token Flows ===

    def record_flow(
        self, flow_type: str, from_addr: str, to_addr: str,
        amount: float, block_height: int = 0, tx_hash: str = "",
    ) -> TokenFlow:
        """Record a token flow event."""
        flow_id = f"flow-{secrets.token_hex(8)}"
        flow = TokenFlow(
            id=flow_id, flow_type=flow_type, from_addr=from_addr,
            to_addr=to_addr, amount=amount, block_height=block_height, tx_hash=tx_hash,
        )
        self._flows.append(flow)

        # Update utility metrics
        if flow_type == FlowType.BURN.value:
            self._utility.burned += amount
        elif flow_type == FlowType.STAKE.value:
            self._utility.staked_amount += amount
        elif flow_type == FlowType.UNSTAKE.value:
            self._utility.staked_amount -= amount
        elif flow_type == FlowType.GOVERNANCE.value:
            self._utility.governance_locked += amount
        elif flow_type == FlowType.TREASURY_SPEND.value:
            self._utility.treasury_balance -= amount
        elif flow_type == FlowType.REWARD.value:
            self._utility.transaction_fees += amount

        return flow

    def list_flows(
        self, flow_type: str = None, limit: int = 50,
        from_addr: str = None, to_addr: str = None,
    ) -> list[TokenFlow]:
        flows = list(self._flows)
        if flow_type:
            flows = [f for f in flows if f.flow_type == flow_type]
        if from_addr:
            flows = [f for f in flows if f.from_addr == from_addr]
        if to_addr:
            flows = [f for f in flows if f.to_addr == to_addr]
        flows.reverse()
        return flows[:limit]

    def get_flow_stats(self) -> dict:
        by_type = defaultdict(float)
        for f in self._flows:
            by_type[f.flow_type] += f.amount
        return {
            "total_flows": len(self._flows),
            "total_volume": sum(f.amount for f in self._flows),
            "by_type": dict(by_type),
        }

    # === Utility ===

    def get_utility(self) -> TokenUtility:
        return self._utility

    def update_utility(self, **kwargs) -> TokenUtility:
        for k, v in kwargs.items():
            if hasattr(self._utility, k):
                setattr(self._utility, k, v)
        return self._utility

    # === Dashboard ===

    def get_dashboard(self) -> dict:
        supply = self.get_circulating_supply()
        return {
            "supply": supply,
            "allocations": [a.to_dict() for a in self.get_allocations()],
            "vesting": self.get_vesting_stats(),
            "flows": self.get_flow_stats(),
            "utility": self._utility.to_dict(),
            "investor_allocation": self._investor_allocation,
            "total_supply": self._total_supply,
            "circulating_supply": supply["circulating"],
            "circulating_pct": supply["circulating_pct"],
        }

    def get_token_distribution_chart(self) -> dict:
        """Get distribution data for pie chart."""
        return {
            "labels": [a.type.title() for a in self.get_allocations()],
            "values": [a.total_amount for a in self.get_allocations()],
            "colors": ["#4F46E5", "#22C55E", "#FFA500", "#EF4444", "#8B5CF6", "#06B6D4", "#F59E0B"],
        }

    def get_supply_progression(self, months: int = 12) -> dict:
        """Project supply progression over months."""
        progression = []
        now = datetime.utcnow()
        for month in range(months + 1):
            date = now + timedelta(days=month * 30)
            circulating = self.get_circulating_supply()["circulating"]
            # Add projected releases from vesting
            for s in self._vesting_schedules.values():
                vest_end = datetime.fromisoformat(s.vesting_end.replace("Z", ""))
                if date >= vest_end:
                    circulating += s.total_amount - s.released
            progression.append({
                "month": month,
                "date": date.isoformat(),
                "circulating": round(circulating, 2),
            })
        return {"progression": progression}


_service: Optional[TokenomicsService] = None

def get_tokenomics_service() -> TokenomicsService:
    global _service
    if _service is None:
        _service = TokenomicsService()
    return _service
