"""
Staking Dashboard — Phase 41

Comprehensive staking management with rewards tracking,
network stats, staking calculator, and user positions.
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

logger = get_logger("service.staking_dashboard")


class StakeStatus(str, Enum):
    ACTIVE = "active"
    UNBONDING = "unbonding"
    WITHDRAWN = "withdrawn"
    SLASHED = "slashed"


class RewardStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    COMPOUNDED = "compounded"


@dataclass
class StakePosition:
    id: str
    delegator: str
    validator_id: str
    validator_name: str
    amount: float
    status: str = StakeStatus.ACTIVE.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    unbonding_at: str = ""
    unbonding_period_days: int = 7
    withdrawn_at: str = ""
    rewards_earned: float = 0.0
    apy: float = 17.0  # 12% base + 5% green bonus
    auto_compound: bool = False
    slashes: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RewardEntry:
    id: str
    delegator: str
    validator_id: str
    validator_name: str
    amount: float
    status: str = RewardStatus.PENDING.value
    epoch: int = 0
    block_height: int = 0
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    claimed_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StakingHistoryEvent:
    id: str
    delegator: str
    event_type: str  # stake, unstake, claim, compound, slash, delegate, undelegate
    validator_id: str
    validator_name: str
    amount: float
    details: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValidatorStakingInfo:
    validator_id: str
    name: str
    address: str
    total_staked: float
    delegator_count: int
    commission_rate: float  # percentage
    apy: float
    green_score: int
    grade: str
    active: bool = True
    self_stake: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


class StakingDashboardService:
    """Staking dashboard with positions, rewards, and network stats."""

    def __init__(self, max_history: int = 5000):
        self._positions: dict[str, StakePosition] = {}
        self._rewards: dict[str, list[RewardEntry]] = defaultdict(list)
        self._history: deque = deque(maxlen=max_history)
        self._validators: dict[str, ValidatorStakingInfo] = {}
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._total_staked = 0.0
        self._total_rewards_distributed = 0.0
        self._current_epoch = 1
        self._current_block = 1000
        self._unbonding_period_days = 7
        self._base_apy = 12.0
        self._green_bonus_apy = 5.0
        self._init_default_validators()
        self._total_staked = sum(v.total_staked for v in self._validators.values())

    def _init_default_validators(self):
        """Initialize with default validator staking info."""
        validator_data = [
            ("val-001", "Green Node Alpha", "0xval1", 5_200_000, 12, 5.0, 92, "A", 8_000_000),
            ("val-002", "Eco Validator Beta", "0xval2", 4_100_000, 9, 5.0, 88, "A", 6_500_000),
            ("val-003", "Solar Node Gamma", "0xval3", 3_800_000, 8, 3.0, 85, "A", 5_800_000),
            ("val-004", "Wind Validator Delta", "0xval4", 3_200_000, 7, 3.0, 82, "B", 5_000_000),
            ("val-005", "Hydro Node Epsilon", "0xval5", 2_900_000, 6, 7.0, 78, "B", 4_200_000),
            ("val-006", "Geothermal Zeta", "0xval6", 2_500_000, 5, 7.0, 75, "B", 3_800_000),
            ("val-007", "Green Node Eta", "0xval7", 2_100_000, 4, 10.0, 71, "C", 3_200_000),
        ]
        for vid, name, addr, staked, delegators, commission, green, grade, self_stake in validator_data:
            apy = self._base_apy + (self._green_bonus_apy if green >= 80 else 0)
            self._validators[vid] = ValidatorStakingInfo(
                validator_id=vid, name=name, address=addr,
                total_staked=staked, delegator_count=delegators,
                commission_rate=commission, apy=apy,
                green_score=green, grade=grade, self_stake=self_stake,
            )

    # === Staking ===

    def stake(self, delegator: str, validator_id: str, amount: float, auto_compound: bool = False) -> Optional[StakePosition]:
        """Stake tokens with a validator."""
        validator = self._validators.get(validator_id)
        if not validator or not validator.active:
            return None
        if amount <= 0:
            return None

        position_id = f"stk-{secrets.token_hex(8)}"
        position = StakePosition(
            id=position_id, delegator=delegator,
            validator_id=validator_id, validator_name=validator.name,
            amount=amount, apy=validator.apy, auto_compound=auto_compound,
        )

        with self._lock:
            self._positions[position_id] = position
            validator.total_staked += amount
            validator.delegator_count += 1
            self._total_staked += amount

            self._add_history(delegator, "stake", validator_id, validator.name, amount, f"Staked {amount} VRS")

        logger.info("stake_created", id=position_id, delegator=delegator, validator=validator_id, amount=amount)
        return position

    def unstake(self, position_id: str) -> Optional[StakePosition]:
        """Begin unbonding period for a stake position."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return None

        position.status = StakeStatus.UNBONDING.value
        unbonding_at = datetime.utcnow() + timedelta(days=position.unbonding_period_days)
        position.unbonding_at = unbonding_at.isoformat()

        # Update validator
        validator = self._validators.get(position.validator_id)
        if validator:
            validator.total_staked -= position.amount
            validator.delegator_count -= 1
            self._total_staked -= position.amount

        self._add_history(position.delegator, "unstake", position.validator_id, position.validator_name, position.amount, f"Unstaking {position.amount} VRS")
        return position

    def withdraw(self, position_id: str) -> Optional[StakePosition]:
        """Withdraw an unbonded position."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.UNBONDING.value:
            return None

        # Check unbonding period
        if position.unbonding_at:
            unbond_time = datetime.fromisoformat(position.unbonding_at.replace("Z", ""))
            if datetime.utcnow() < unbond_time:
                return None  # Still unbonding

        position.status = StakeStatus.WITHDRAWN.value
        position.withdrawn_at = datetime.utcnow().isoformat()
        self._add_history(position.delegator, "withdraw", position.validator_id, position.validator_name, position.amount, f"Withdrawn {position.amount} VRS")
        return position

    def slash(self, position_id: str, percentage: float = 5.0) -> Optional[StakePosition]:
        """Slash a position (penalty)."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return None

        slash_amount = position.amount * (percentage / 100)
        position.amount -= slash_amount
        position.slashes += 1

        if position.amount <= 0:
            position.status = StakeStatus.SLASHEDED.value

        self._add_history(position.delegator, "slash", position.validator_id, position.validator_name, slash_amount, f"Slashed {slash_amount} VRS ({percentage}%)")
        return position

    def get_position(self, position_id: str) -> Optional[StakePosition]:
        return self._positions.get(position_id)

    def list_positions(self, delegator: str = None, validator_id: str = None, status: str = None, limit: int = 50) -> list[StakePosition]:
        positions = list(self._positions.values())
        if delegator:
            positions = [p for p in positions if p.delegator == delegator]
        if validator_id:
            positions = [p for p in positions if p.validator_id == validator_id]
        if status:
            positions = [p for p in positions if p.status == status]
        positions.sort(key=lambda p: p.created, reverse=True)
        return positions[:limit]

    def toggle_auto_compound(self, position_id: str) -> Optional[StakePosition]:
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return None
        position.auto_compound = not position.auto_compound
        return position

    # === Rewards ===

    def calculate_rewards(self, position_id: str) -> float:
        """Calculate pending rewards for a position."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return 0.0

        # Simple APY calculation based on days staked
        created = datetime.fromisoformat(position.created.replace("Z", ""))
        days_staked = max(1, (datetime.utcnow() - created).days)
        daily_rate = position.apy / 100 / 365
        rewards = position.amount * daily_rate * days_staked

        # Subtract already earned
        rewards -= position.rewards_earned
        return max(0, round(rewards, 4))

    def claim_rewards(self, position_id: str) -> Optional[RewardEntry]:
        """Claim pending rewards."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return None

        pending = self.calculate_rewards(position_id)
        if pending <= 0:
            return None

        reward_id = f"rwd-{secrets.token_hex(8)}"
        reward = RewardEntry(
            id=reward_id, delegator=position.delegator,
            validator_id=position.validator_id, validator_name=position.validator_name,
            amount=pending, status=RewardStatus.CLAIMED.value,
            epoch=self._current_epoch, block_height=self._current_block,
            claimed_at=datetime.utcnow().isoformat(),
        )

        position.rewards_earned += pending
        self._rewards[position.delegator].append(reward)
        self._total_rewards_distributed += pending

        self._add_history(position.delegator, "claim", position.validator_id, position.validator_name, pending, f"Claimed {pending} VRS rewards")
        return reward

    def compound_rewards(self, position_id: str) -> Optional[StakePosition]:
        """Compound rewards back into the stake."""
        position = self._positions.get(position_id)
        if not position or position.status != StakeStatus.ACTIVE.value:
            return None

        pending = self.calculate_rewards(position_id)
        if pending <= 0:
            return None

        position.amount += pending
        position.rewards_earned += pending
        self._total_staked += pending

        # Create reward entry as compounded
        reward_id = f"rwd-{secrets.token_hex(8)}"
        reward = RewardEntry(
            id=reward_id, delegator=position.delegator,
            validator_id=position.validator_id, validator_name=position.validator_name,
            amount=pending, status=RewardStatus.COMPOUNDED.value,
            epoch=self._current_epoch, block_height=self._current_block,
        )
        self._rewards[position.delegator].append(reward)
        self._total_rewards_distributed += pending

        self._add_history(position.delegator, "compound", position.validator_id, position.validator_name, pending, f"Compounded {pending} VRS")
        return position

    def list_rewards(self, delegator: str, status: str = None, limit: int = 50) -> list[RewardEntry]:
        rewards = self._rewards.get(delegator, [])
        if status:
            rewards = [r for r in rewards if r.status == status]
        return sorted(rewards, key=lambda r: r.created, reverse=True)[:limit]

    def get_total_rewards(self, delegator: str) -> dict:
        rewards = self._rewards.get(delegator, [])
        claimed = sum(r.amount for r in rewards if r.status == RewardStatus.CLAIMED.value)
        compounded = sum(r.amount for r in rewards if r.status == RewardStatus.COMPOUNDED.value)
        pending = sum(self.calculate_rewards(p.id) for p in self.list_positions(delegator) if p.status == StakeStatus.ACTIVE.value)
        return {
            "total_claimed": round(claimed, 4),
            "total_compounded": round(compounded, 4),
            "pending": round(pending, 4),
            "total_earned": round(claimed + compounded + pending, 4),
        }

    # === Validators ===

    def list_validators(self, active_only: bool = True, sort_by: str = "total_staked", limit: int = 50) -> list[ValidatorStakingInfo]:
        validators = list(self._validators.values())
        if active_only:
            validators = [v for v in validators if v.active]

        sort_map = {
            "total_staked": lambda v: v.total_staked,
            "apy": lambda v: v.apy,
            "green_score": lambda v: v.green_score,
            "commission": lambda v: v.commission_rate,
            "delegators": lambda v: v.delegator_count,
        }
        validators.sort(key=sort_map.get(sort_by, lambda v: v.total_staked), reverse=True)
        return validators[:limit]

    def get_validator(self, validator_id: str) -> Optional[ValidatorStakingInfo]:
        return self._validators.get(validator_id)

    # === Calculator ===

    def calculate_staking_projection(self, amount: float, apy: float, days: int, compound: bool = False) -> dict:
        """Calculate projected staking returns."""
        if compound:
            # Compound daily
            daily_rate = apy / 100 / 365
            final_amount = amount * ((1 + daily_rate) ** days)
            rewards = final_amount - amount
        else:
            # Simple interest
            rewards = amount * (apy / 100) * (days / 365)

        return {
            "principal": amount,
            "apy": apy,
            "days": days,
            "projected_rewards": round(rewards, 4),
            "projected_total": round(amount + rewards, 4),
            "compound": compound,
            "daily_rewards": round(rewards / days, 4) if days > 0 else 0,
        }

    # === History ===

    def _add_history(self, delegator: str, event_type: str, validator_id: str, validator_name: str, amount: float, details: str = ""):
        event = StakingHistoryEvent(
            id=f"his-{secrets.token_hex(8)}", delegator=delegator,
            event_type=event_type, validator_id=validator_id,
            validator_name=validator_name, amount=amount, details=details,
        )
        self._history.append(event)

    def list_history(self, delegator: str = None, event_type: str = None, limit: int = 50) -> list[StakingHistoryEvent]:
        events = list(self._history)
        if delegator:
            events = [e for e in events if e.delegator == delegator]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        events.sort(key=lambda e: e.created, reverse=True)
        return events[:limit]

    # === Network Stats ===

    def get_network_stats(self) -> dict:
        total_validators = len(self._validators)
        active_validators = sum(1 for v in self._validators.values() if v.active)
        total_delegators = len(set(p.delegator for p in self._positions.values()))
        avg_apy = sum(v.apy for v in self._validators.values()) / max(1, total_validators)
        avg_commission = sum(v.commission_rate for v in self._validators.values()) / max(1, total_validators)
        max_validator = max(self._validators.values(), key=lambda v: v.total_staked) if self._validators else None
        min_validator = min(self._validators.values(), key=lambda v: v.total_staked) if self._validators else None

        total_possible_stake = 100_000_000_000  # 100B total supply
        staking_ratio = (self._total_staked / total_possible_stake) * 100 if total_possible_stake > 0 else 0

        return {
            "total_staked": round(self._total_staked, 2),
            "staking_ratio": round(staking_ratio, 4),
            "total_validators": total_validators,
            "active_validators": active_validators,
            "total_delegators": total_delegators,
            "avg_apy": round(avg_apy, 2),
            "avg_commission": round(avg_commission, 2),
            "total_rewards_distributed": round(self._total_rewards_distributed, 2),
            "current_epoch": self._current_epoch,
            "current_block": self._current_block,
            "unbonding_period_days": self._unbonding_period_days,
            "base_apy": self._base_apy,
            "green_bonus_apy": self._green_bonus_apy,
            "largest_validator": max_validator.name if max_validator else "",
            "smallest_validator": min_validator.name if min_validator else "",
        }

    # === User Dashboard ===

    def get_user_dashboard(self, delegator: str) -> dict:
        positions = self.list_positions(delegator)
        active_positions = [p for p in positions if p.status == StakeStatus.ACTIVE.value]
        total_staked = sum(p.amount for p in active_positions)
        rewards_info = self.get_total_rewards(delegator)
        pending_rewards = sum(self.calculate_rewards(p.id) for p in active_positions)

        by_validator = defaultdict(float)
        for p in active_positions:
            by_validator[p.validator_name] += p.amount

        return {
            "total_staked": round(total_staked, 2),
            "active_positions": len(active_positions),
            "total_positions": len(positions),
            "rewards": rewards_info,
            "pending_rewards": round(pending_rewards, 4),
            "positions": [p.to_dict() for p in positions[:20]],
            "by_validator": dict(by_validator),
            "recent_rewards": [r.to_dict() for r in self.list_rewards(delegator, limit=10)],
            "recent_history": [h.to_dict() for h in self.list_history(delegator, limit=10)],
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 30):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("staking_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                self._current_block += 1
                if self._current_block % 100 == 0:
                    self._current_epoch += 1
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Main Dashboard ===

    def get_dashboard(self, delegator: str = "0xverdis") -> dict:
        return {
            "network": self.get_network_stats(),
            "user": self.get_user_dashboard(delegator),
            "top_validators": [v.to_dict() for v in self.list_validators(sort_by="total_staked", limit=10)],
            "monitoring": self._monitoring,
        }


_service: Optional[StakingDashboardService] = None

def get_staking_dashboard_service() -> StakingDashboardService:
    global _service
    if _service is None:
        _service = StakingDashboardService()
    return _service
