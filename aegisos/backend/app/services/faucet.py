"""
Faucet Service — Phase 46

Testnet token distribution with rate limiting, captcha verification,
request tracking, and anti-abuse measures.
"""

import secrets
import time
import threading
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.faucet")


class FaucetStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DEPLETED = "depleted"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DISTRIBUTED = "distributed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class FaucetRequest:
    id: str
    address: str
    amount: float
    ip_address: str = ""
    user_agent: str = ""
    captcha_verified: bool = False
    status: str = RequestStatus.PENDING.value
    tx_hash: str = ""
    error: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    processed: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FaucetConfig:
    drip_amount: float = 100.0  # VRS per request
    cooldown_hours: int = 24  # Per address
    ip_cooldown_hours: int = 12  # Per IP
    daily_limit: float = 10000.0  # Max per day
    max_pending: int = 10  # Max pending requests
    total_supply: float = 10_000_000.0  # Faucet reserve
    distributed: float = 0.0
    min_balance: float = 1000.0  # Auto-pause below this
    captcha_required: bool = True
    whitelist_enabled: bool = False
    network: str = "testnet"
    chain_id: int = 909
    rpc_url: str = "https://testnet.verdischain.com"
    status: str = FaucetStatus.ACTIVE.value

    def to_dict(self) -> dict:
        return asdict(self)


class FaucetService:
    """Testnet faucet with rate limiting and anti-abuse."""

    def __init__(self, max_history: int = 10000):
        self._requests: dict[str, FaucetRequest] = {}
        self._history: deque = deque(maxlen=max_history)
        self._last_claim: dict[str, str] = {}  # address -> last claim ISO
        self._last_ip_claim: dict[str, str] = {}  # ip -> last claim ISO
        self._daily_distributed: dict[str, float] = defaultdict(float)  # date -> amount
        self._whitelist: set = set()
        self._blacklist: set = set()
        self._captcha_challenges: dict[str, dict] = {}
        self._config = FaucetConfig()
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_sample_requests()

    def _init_sample_requests(self):
        """Initialize with sample faucet requests."""
        import random
        random.seed(42)
        for i in range(50):
            req = FaucetRequest(
                id=f"freq-{secrets.token_hex(8)}",
                address=f"0x{secrets.token_hex(20)}",
                amount=self._config.drip_amount,
                ip_address=f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
                captcha_verified=True,
                status=random.choices(
                    [RequestStatus.DISTRIBUTED.value, RequestStatus.FAILED.value, RequestStatus.REJECTED.value],
                    weights=[85, 10, 5]
                )[0],
                created=(datetime.utcnow() - timedelta(hours=random.randint(0, 168))).isoformat(),
                processed=(datetime.utcnow() - timedelta(hours=random.randint(0, 160))).isoformat(),
            )
            self._requests[req.id] = req
            self._history.append(req)
            if req.status == RequestStatus.DISTRIBUTED.value:
                self._config.distributed += req.amount
                self._last_claim[req.address] = req.processed

    # === Captcha ===

    def generate_captcha(self) -> dict:
        """Generate a simple math captcha challenge."""
        a = secrets.randbelow(20) + 1
        b = secrets.randbelow(20) + 1
        challenge_id = secrets.token_hex(16)
        answer = str(a + b)
        self._captcha_challenges[challenge_id] = {
            "answer": answer,
            "expires": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        }
        return {
            "challenge_id": challenge_id,
            "question": f"What is {a} + {b}?",
            "expires_in": 300,
        }

    def verify_captcha(self, challenge_id: str, answer: str) -> bool:
        """Verify a captcha challenge."""
        challenge = self._captcha_challenges.get(challenge_id)
        if not challenge:
            return False
        if datetime.utcnow() > datetime.fromisoformat(challenge["expires"].replace("Z", "")):
            del self._captcha_challenges[challenge_id]
            return False
        if challenge["answer"] == answer.strip():
            del self._captcha_challenges[challenge_id]
            return True
        return False

    # === Claim ===

    def request_tokens(self, address: str, ip_address: str = "",
                       user_agent: str = "", captcha_id: str = "",
                       captcha_answer: str = "") -> dict:
        """Request testnet tokens from the faucet."""
        # Check faucet status
        if self._config.status != FaucetStatus.ACTIVE.value:
            return {"error": f"Faucet is {self._config.status}"}

        # Check balance
        remaining = self._config.total_supply - self._config.distributed
        if remaining < self._config.min_balance:
            self._config.status = FaucetStatus.DEPLETED.value
            return {"error": "Faucet depleted"}

        # Check blacklist
        if address in self._blacklist:
            return {"error": "Address is blacklisted"}

        # Check whitelist
        if self._config.whitelist_enabled and address not in self._whitelist:
            return {"error": "Address not whitelisted"}

        # Check captcha
        if self._config.captcha_required:
            if not captcha_id or not captcha_answer:
                return {"error": "Captcha required", "captcha": self.generate_captcha()}
            if not self.verify_captcha(captcha_id, captcha_answer):
                return {"error": "Captcha verification failed", "captcha": self.generate_captcha()}

        # Check address cooldown
        last = self._last_claim.get(address)
        if last:
            last_time = datetime.fromisoformat(last.replace("Z", ""))
            elapsed = datetime.utcnow() - last_time
            if elapsed < timedelta(hours=self._config.cooldown_hours):
                remaining_hours = (timedelta(hours=self._config.cooldown_hours) - elapsed).total_seconds() / 3600
                return {"error": f"Cooldown active. Try again in {remaining_hours:.1f} hours"}

        # Check IP cooldown
        if ip_address:
            last_ip = self._last_ip_claim.get(ip_address)
            if last_ip:
                last_ip_time = datetime.fromisoformat(last_ip.replace("Z", ""))
                elapsed = datetime.utcnow() - last_ip_time
                if elapsed < timedelta(hours=self._config.ip_cooldown_hours):
                    return {"error": "IP cooldown active"}

        # Check daily limit
        today = datetime.utcnow().date().isoformat()
        if self._daily_distributed[today] >= self._config.daily_limit:
            return {"error": "Daily distribution limit reached"}

        # Check pending requests
        pending = sum(1 for r in self._requests.values()
                      if r.address == address and r.status == RequestStatus.PENDING.value)
        if pending >= self._config.max_pending:
            return {"error": "Too many pending requests"}

        # Create request
        req_id = f"freq-{secrets.token_hex(8)}"
        amount = self._config.drip_amount

        # If daily limit would be exceeded, reduce amount
        if self._daily_distributed[today] + amount > self._config.daily_limit:
            amount = self._config.daily_limit - self._daily_distributed[today]

        req = FaucetRequest(
            id=req_id, address=address, amount=amount,
            ip_address=ip_address, user_agent=user_agent,
            captcha_verified=True, status=RequestStatus.APPROVED.value,
        )

        with self._lock:
            self._requests[req_id] = req
            self._history.append(req)

            # Process immediately (simulated)
            req.status = RequestStatus.DISTRIBUTED.value
            req.tx_hash = f"0x{secrets.token_hex(32)}"
            req.processed = datetime.utcnow().isoformat()

            self._config.distributed += amount
            self._daily_distributed[today] += amount
            self._last_claim[address] = req.processed
            if ip_address:
                self._last_ip_claim[ip_address] = req.processed

        logger.info("faucet_distributed", id=req_id, address=address, amount=amount)
        return {
            "request_id": req_id,
            "status": "distributed",
            "amount": amount,
            "tx_hash": req.tx_hash,
            "address": address,
            "remaining_supply": round(self._config.total_supply - self._config.distributed, 2),
        }

    # === Queries ===

    def get_request(self, request_id: str) -> Optional[FaucetRequest]:
        return self._requests.get(request_id)

    def list_requests(self, address: str = None, status: str = None,
                      limit: int = 50) -> list[FaucetRequest]:
        requests = list(self._requests.values())
        if address:
            requests = [r for r in requests if r.address == address]
        if status:
            requests = [r for r in requests if r.status == status]
        requests.sort(key=lambda r: r.created, reverse=True)
        return requests[:limit]

    def get_address_info(self, address: str) -> dict:
        """Get faucet info for a specific address."""
        last_claim = self._last_claim.get(address)
        cooldown_remaining = 0
        if last_claim:
            last_time = datetime.fromisoformat(last_claim.replace("Z", ""))
            elapsed = datetime.utcnow() - last_time
            cooldown = timedelta(hours=self._config.cooldown_hours)
            if elapsed < cooldown:
                cooldown_remaining = round((cooldown - elapsed).total_seconds() / 3600, 1)

        claims = [r for r in self._requests.values() if r.address == address and r.status == "distributed"]
        total_received = sum(r.amount for r in claims)

        return {
            "address": address,
            "total_claims": len(claims),
            "total_received": round(total_received, 2),
            "last_claim": last_claim or "",
            "cooldown_remaining_hours": cooldown_remaining,
            "can_claim": cooldown_remaining == 0 and address not in self._blacklist,
            "blacklisted": address in self._blacklist,
            "whitelisted": address in self._whitelist,
        }

    # === Config ===

    def get_config(self) -> dict:
        remaining = self._config.total_supply - self._config.distributed
        return {
            **self._config.to_dict(),
            "remaining_supply": round(remaining, 2),
            "remaining_percentage": round(remaining / max(1, self._config.total_supply) * 100, 2),
        }

    def update_config(self, **kwargs) -> dict:
        for k, v in kwargs.items():
            if hasattr(self._config, k):
                setattr(self._config, k, v)
        return self.get_config()

    def pause(self) -> dict:
        self._config.status = FaucetStatus.PAUSED.value
        return {"status": "paused"}

    def resume(self) -> dict:
        remaining = self._config.total_supply - self._config.distributed
        if remaining < self._config.min_balance:
            return {"error": "Cannot resume: supply too low"}
        self._config.status = FaucetStatus.ACTIVE.value
        return {"status": "active"}

    def refill(self, amount: float) -> dict:
        self._config.total_supply += amount
        if self._config.status == FaucetStatus.DEPLETED.value:
            self._config.status = FaucetStatus.ACTIVE.value
        return self.get_config()

    # === Whitelist / Blacklist ===

    def add_to_whitelist(self, address: str) -> bool:
        self._whitelist.add(address)
        return True

    def remove_from_whitelist(self, address: str) -> bool:
        return self._whitelist.discard(address) is None or address not in self._whitelist

    def add_to_blacklist(self, address: str) -> bool:
        self._blacklist.add(address)
        return True

    def remove_from_blacklist(self, address: str) -> bool:
        self._blacklist.discard(address)
        return True

    def get_whitelist(self) -> list[str]:
        return sorted(list(self._whitelist))

    def get_blacklist(self) -> list[str]:
        return sorted(list(self._blacklist))

    # === Stats ===

    def get_stats(self) -> dict:
        today = datetime.utcnow().date().isoformat()
        total_requests = len(self._requests)
        distributed = sum(1 for r in self._requests.values() if r.status == "distributed")
        failed = sum(1 for r in self._requests.values() if r.status == "failed")
        rejected = sum(1 for r in self._requests.values() if r.status == "rejected")
        pending = sum(1 for r in self._requests.values() if r.status == "pending")

        unique_addresses = len(set(r.address for r in self._requests.values()))
        remaining = self._config.total_supply - self._config.distributed

        return {
            "status": self._config.status,
            "total_supply": self._config.total_supply,
            "distributed": round(self._config.distributed, 2),
            "remaining": round(remaining, 2),
            "remaining_percentage": round(remaining / max(1, self._config.total_supply) * 100, 2),
            "total_requests": total_requests,
            "distributed_count": distributed,
            "failed_count": failed,
            "rejected_count": rejected,
            "pending_count": pending,
            "unique_addresses": unique_addresses,
            "today_distributed": round(self._daily_distributed.get(today, 0), 2),
            "daily_limit": self._config.daily_limit,
            "drip_amount": self._config.drip_amount,
            "cooldown_hours": self._config.cooldown_hours,
            "whitelist_size": len(self._whitelist),
            "blacklist_size": len(self._blacklist),
        }

    def get_dashboard(self) -> dict:
        return {
            "stats": self.get_stats(),
            "config": self.get_config(),
            "recent_requests": [r.to_dict() for r in self.list_requests(limit=10)],
            "top_claimers": self._get_top_claimers(10),
            "monitoring": self._monitoring,
        }

    def _get_top_claimers(self, limit: int) -> list[dict]:
        claimers = defaultdict(lambda: {"total": 0.0, "count": 0})
        for r in self._requests.values():
            if r.status == "distributed":
                claimers[r.address]["total"] += r.amount
                claimers[r.address]["count"] += 1
        top = sorted(claimers.items(), key=lambda x: x[1]["total"], reverse=True)[:limit]
        return [{"address": addr, "total": round(data["total"], 2), "claims": data["count"]} for addr, data in top]

    # === Monitoring ===

    def start_monitoring(self, interval: int = 300):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("faucet_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Auto-pause if depleted
                remaining = self._config.total_supply - self._config.distributed
                if remaining < self._config.min_balance and self._config.status == "active":
                    self._config.status = FaucetStatus.DEPLETED.value
                    logger.warning("faucet_auto_depleted", remaining=remaining)

                # Clean expired captcha challenges
                now = datetime.utcnow()
                expired = [k for k, v in self._captcha_challenges.items()
                           if now > datetime.fromisoformat(v["expires"].replace("Z", ""))]
                for k in expired:
                    del self._captcha_challenges[k]

                # Reset daily distribution at midnight
                today = now.date().isoformat()
                yesterday = (now - timedelta(days=1)).date().isoformat()
                if yesterday in self._daily_distributed:
                    # Keep history but new day starts fresh
                    pass

            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring


_service: Optional[FaucetService] = None

def get_faucet_service() -> FaucetService:
    global _service
    if _service is None:
        _service = FaucetService()
    return _service
