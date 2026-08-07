"""
Validator Management — Phase 37

Validator registration, health monitoring, green scoring,
staking delegation, performance metrics, and network status.
"""

import secrets
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from app.core.logging import get_logger

logger = get_logger("service.validators")


class ValidatorStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    SLASHED = "slashed"
    EJECTED = "ejected"


class ValidatorGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass
class Validator:
    id: str
    address: str
    name: str
    status: str = ValidatorStatus.ACTIVE.value
    joined: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    blocks_produced: int = 0
    blocks_missed: int = 0
    uptime_pct: float = 100.0
    total_stake: float = 0
    self_stake: float = 0
    delegator_stake: float = 0
    reward_rate: float = 0.0  # APY %
    commission_rate: float = 0.0  # commission %
    green_score: float = 0.0  # 0-100
    energy_source: str = "unknown"
    carbon_offset: float = 0.0  # tonnes CO2
    certified: bool = False
    website: str = ""
    description: str = ""
    avatar: str = ""
    last_active: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    rank: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Delegation:
    id: str
    delegator: str
    validator_id: str
    amount: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    rewards_earned: float = 0.0
    active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ValidatorEvent:
    id: str
    validator_id: str
    event_type: str  # block_produced, block_missed, slashed, rewarded, joined, left
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    block_height: int = 0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class ValidatorService:
    """Validator management, monitoring, and staking delegation."""

    def __init__(self, max_validators: int = 101):
        self._max_validators = max_validators
        self._validators: dict[str, Validator] = {}
        self._address_to_id: dict[str, str] = {}
        self._delegations: dict[str, list[Delegation]] = defaultdict(list)
        self._events: list[ValidatorEvent] = []
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_default_validators()

    def _init_default_validators(self):
        """Initialize with the 14 live validators."""
        for i in range(1, 15):
            self.register_validator(
                address=f"0x{'a' * 38}{i:02d}",
                name=f"Verdis Validator #{i:02d}",
                energy_source="solar" if i % 3 == 0 else "hydro" if i % 3 == 1 else "wind",
                green_score=75.0 + (i * 1.5),
                carbon_offset=100.0 + (i * 10),
                certified=i % 2 == 0,
                total_stake=5_000_000 + (i * 500_000),
                self_stake=1_000_000 + (i * 100_000),
                commission_rate=5.0 + (i % 3),
            )

    def register_validator(
        self, address: str, name: str, energy_source: str = "unknown",
        green_score: float = 0.0, carbon_offset: float = 0.0,
        certified: bool = False, total_stake: float = 0,
        self_stake: float = 0, commission_rate: float = 0.0,
        website: str = "", description: str = "",
    ) -> Validator:
        """Register a new validator."""
        with self._lock:
            if address in self._address_to_id:
                return self._validators[self._address_to_id[address]]

            if len(self._validators) >= self._max_validators:
                raise ValueError("Maximum validator count reached")

            validator_id = f"val-{secrets.token_hex(8)}"
            delegator_stake = total_stake - self_stake

            validator = Validator(
                id=validator_id, address=address, name=name,
                energy_source=energy_source, green_score=green_score,
                carbon_offset=carbon_offset, certified=certified,
                total_stake=total_stake, self_stake=self_stake,
                delegator_stake=delegator_stake,
                commission_rate=commission_rate,
                website=website, description=description,
                reward_rate=self._calculate_reward_rate(green_score, total_stake),
            )

            self._validators[validator_id] = validator
            self._address_to_id[address] = validator_id

            self._record_event(validator_id, "joined", details={"name": name, "address": address})
            self._update_ranks()

            logger.info("validator_registered", id=validator_id, name=name, address=address)
            return validator

    def _calculate_reward_rate(self, green_score: float, total_stake: float) -> float:
        """Calculate APY based on green score and stake."""
        base_rate = 12.0  # 12% base APY
        green_bonus = (green_score / 100) * 5.0  # Up to 5% bonus for green
        stake_factor = min(1.0, 5_000_000 / max(1, total_stake))  # Lower rate for big validators
        return round(base_rate + green_bonus * stake_factor, 2)

    def remove_validator(self, validator_id: str) -> bool:
        """Remove a validator."""
        with self._lock:
            v = self._validators.get(validator_id)
            if not v:
                return False
            v.status = ValidatorStatus.EJECTED.value
            self._record_event(validator_id, "left")
            self._update_ranks()
            return True

    def pause_validator(self, validator_id: str) -> bool:
        v = self._validators.get(validator_id)
        if not v or v.status != ValidatorStatus.ACTIVE.value:
            return False
        v.status = ValidatorStatus.PAUSED.value
        return True

    def activate_validator(self, validator_id: str) -> bool:
        v = self._validators.get(validator_id)
        if not v or v.status != ValidatorStatus.PAUSED.value:
            return False
        v.status = ValidatorStatus.ACTIVE.value
        return True

    def slash_validator(self, validator_id: str, reason: str = "misbehavior") -> bool:
        v = self._validators.get(validator_id)
        if not v:
            return False
        v.status = ValidatorStatus.SLASHED.value
        slash_amount = v.total_stake * 0.05  # 5% slashing
        v.total_stake -= slash_amount
        self._record_event(validator_id, "slashed", details={"reason": reason, "amount": slash_amount})
        return True

    def get_validator(self, validator_id: str) -> Optional[Validator]:
        return self._validators.get(validator_id)

    def get_validator_by_address(self, address: str) -> Optional[Validator]:
        vid = self._address_to_id.get(address)
        return self._validators.get(vid) if vid else None

    def list_validators(
        self, status: str = None, certified: bool = None,
        sort_by: str = "stake", limit: int = 101,
    ) -> list[Validator]:
        validators = list(self._validators.values())
        if status:
            validators = [v for v in validators if v.status == status]
        if certified is not None:
            validators = [v for v in validators if v.certified == certified]

        sort_map = {
            "stake": lambda v: v.total_stake,
            "green": lambda v: v.green_score,
            "uptime": lambda v: v.uptime_pct,
            "reward": lambda v: v.reward_rate,
            "blocks": lambda v: v.blocks_produced,
        }
        validators.sort(key=sort_map.get(sort_by, lambda v: v.total_stake), reverse=True)
        return validators[:limit]

    def _update_ranks(self):
        """Update validator ranks by total stake."""
        sorted_vals = sorted(self._validators.values(), key=lambda v: v.total_stake, reverse=True)
        for i, v in enumerate(sorted_vals):
            v.rank = i + 1

    # === Monitoring ===

    def record_block_production(self, validator_id: str, produced: bool):
        """Record a block production event."""
        v = self._validators.get(validator_id)
        if not v:
            return

        if produced:
            v.blocks_produced += 1
            self._record_event(validator_id, "block_produced", block_height=v.blocks_produced)
        else:
            v.blocks_missed += 1
            self._record_event(validator_id, "block_missed", block_height=v.blocks_produced + v.blocks_missed)

        # Update uptime
        total = v.blocks_produced + v.blocks_missed
        if total > 0:
            v.uptime_pct = round((v.blocks_produced / total) * 100, 2)

        v.last_active = datetime.utcnow().isoformat()

    def update_green_score(self, validator_id: str, score: float, energy_source: str = None, carbon_offset: float = None):
        """Update a validator's green score."""
        v = self._validators.get(validator_id)
        if not v:
            return None
        v.green_score = max(0, min(100, score))
        if energy_source:
            v.energy_source = energy_source
        if carbon_offset is not None:
            v.carbon_offset = carbon_offset
        # Update reward rate based on new green score
        v.reward_rate = self._calculate_reward_rate(v.green_score, v.total_stake)
        if v.green_score >= 80:
            v.certified = True
        return v

    def certify_validator(self, validator_id: str) -> bool:
        v = self._validators.get(validator_id)
        if not v or v.green_score < 80:
            return False
        v.certified = True
        return True

    # === Delegation ===

    def delegate(
        self, delegator: str, validator_id: str, amount: float,
    ) -> Optional[Delegation]:
        """Delegate stake to a validator."""
        v = self._validators.get(validator_id)
        if not v or v.status != ValidatorStatus.ACTIVE.value:
            return None

        delegation_id = f"del-{secrets.token_hex(8)}"
        delegation = Delegation(
            id=delegation_id, delegator=delegator,
            validator_id=validator_id, amount=amount,
        )
        self._delegations[validator_id].append(delegation)
        v.delegator_stake += amount
        v.total_stake += amount
        v.reward_rate = self._calculate_reward_rate(v.green_score, v.total_stake)
        self._update_ranks()

        logger.info("delegation_created", id=delegation_id, validator=validator_id, amount=amount)
        return delegation

    def undelegate(self, delegation_id: str) -> bool:
        """Remove a delegation."""
        for vid, dels in self._delegations.items():
            for d in dels:
                if d.id == delegation_id and d.active:
                    d.active = False
                    v = self._validators.get(vid)
                    if v:
                        v.delegator_stake -= d.amount
                        v.total_stake -= d.amount
                        v.reward_rate = self._calculate_reward_rate(v.green_score, v.total_stake)
                        self._update_ranks()
                    return True
        return False

    def list_delegations(self, validator_id: str = None, delegator: str = None) -> list[Delegation]:
        if validator_id:
            dels = self._delegations.get(validator_id, [])
        else:
            dels = [d for dl in self._delegations.values() for d in dl]
        if delegator:
            dels = [d for d in dels if d.delegator == delegator]
        return dels

    # === Events ===

    def _record_event(self, validator_id: str, event_type: str, block_height: int = 0, details: dict = None):
        event = ValidatorEvent(
            id=f"evt-{secrets.token_hex(8)}",
            validator_id=validator_id, event_type=event_type,
            block_height=block_height, details=details or {},
        )
        self._events.append(event)
        # Keep only last 5000 events
        if len(self._events) > 5000:
            self._events = self._events[-5000:]

    def get_validator_events(self, validator_id: str, limit: int = 50) -> list[ValidatorEvent]:
        return [e for e in self._events if e.validator_id == validator_id][-limit:]

    def get_recent_events(self, limit: int = 50) -> list[ValidatorEvent]:
        return self._events[-limit:]

    # === Background Monitoring ===

    def start_monitoring(self, interval: int = 6):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("validator_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        import random
        while self._monitoring:
            try:
                active = [v for v in self._validators.values() if v.status == "active"]
                if active:
                    # Simulate block production round
                    producer = random.choice(active)
                    produced = random.random() > 0.05  # 95% success rate
                    self.record_block_production(producer.id, produced)
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring

    # === Stats ===

    def get_network_stats(self) -> dict:
        validators = list(self._validators.values())
        active = [v for v in validators if v.status == "active"]
        total_stake = sum(v.total_stake for v in validators)
        avg_green = sum(v.green_score for v in validators) / max(1, len(validators))
        avg_uptime = sum(v.uptime_pct for v in validators) / max(1, len(validators))
        certified = sum(1 for v in validators if v.certified)

        return {
            "total_validators": len(validators),
            "active_validators": len(active),
            "max_validators": self._max_validators,
            "total_stake": total_stake,
            "avg_green_score": round(avg_green, 2),
            "avg_uptime": round(avg_uptime, 2),
            "certified_validators": certified,
            "total_carbon_offset": sum(v.carbon_offset for v in validators),
            "total_blocks_produced": sum(v.blocks_produced for v in validators),
            "total_delegations": sum(len(d) for d in self._delegations.values()),
            "monitoring": self._monitoring,
        }

    def get_validator_grade(self, validator_id: str) -> str:
        """Get letter grade for a validator based on green score and uptime."""
        v = self._validators.get(validator_id)
        if not v:
            return "D"
        combined = (v.green_score * 0.4 + v.uptime_pct * 0.4 + min(100, v.total_stake / 100000) * 0.2)
        if combined >= 90:
            return "A"
        elif combined >= 75:
            return "B"
        elif combined >= 60:
            return "C"
        else:
            return "D"

    def get_dashboard(self) -> dict:
        stats = self.get_network_stats()
        top_validators = [v.to_dict() for v in self.list_validators(sort_by="stake", limit=10)]
        greenest = [v.to_dict() for v in self.list_validators(sort_by="green", limit=5)]
        return {
            "stats": stats,
            "top_validators": top_validators,
            "greenest_validators": greenest,
            "recent_events": [e.to_dict() for e in self.get_recent_events(20)],
        }


_service: Optional[ValidatorService] = None

def get_validator_service() -> ValidatorService:
    global _service
    if _service is None:
        _service = ValidatorService()
    return _service
