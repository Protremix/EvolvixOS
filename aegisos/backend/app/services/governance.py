"""
Governance & Treasury Management — Phase 35

Proposal creation, voting, treasury allocation, council management.
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

logger = get_logger("service.governance")


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ProposalType(str, Enum):
    REFERENDUM = "referendum"
    TREASURY_SPEND = "treasury_spend"
    COUNCIL_MOTION = "council_motion"
    RUNTIME_UPGRADE = "runtime_upgrade"
    PARAMETER_CHANGE = "parameter_change"
    EMERGENCY = "emergency"


class VoteType(str, Enum):
    AYE = "aye"
    NAY = "nay"
    ABSTAIN = "abstain"


class TreasuryStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    EXPIRED = "expired"


@dataclass
class Proposal:
    id: str
    type: str
    title: str
    description: str
    proposer: str
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = ProposalStatus.PROPOSED.value
    voting_start: str = ""
    voting_end: str = ""
    aye_votes: int = 0
    nay_votes: int = 0
    abstain_votes: int = 0
    total_voters: int = 0
    threshold: float = 0.5  # 50% + 1
    proposal_data: dict = field(default_factory=dict)
    execution_hash: str = ""
    executed_at: str = ""
    block_height: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Vote:
    proposal_id: str
    voter: str
    vote_type: str
    voting_power: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TreasuryProposal:
    id: str
    title: str
    description: str
    proposer: str
    beneficiary: str
    amount: float
    currency: str = "VRS"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = TreasuryStatus.PENDING.value
    approvals: int = 0
    rejections: int = 0
    threshold: int = 3  # council approvals needed
    disbursement_tx: str = ""
    disbursement_date: str = ""
    expires_at: str = ""
    category: str = "general"  # general, eco, infra, marketing, dev
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CouncilMember:
    address: str
    name: str
    joined: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    votes_cast: int = 0
    proposals_created: int = 0
    active: bool = True
    term_end: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class GovernanceService:
    """Governance, voting, treasury, and council management."""

    def __init__(self, voting_period_days: int = 7):
        self._voting_period_days = voting_period_days
        self._proposals: dict[str, Proposal] = {}
        self._votes: dict[str, list[Vote]] = defaultdict(list)  # proposal_id -> votes
        self._treasury_proposals: dict[str, TreasuryProposal] = {}
        self._council: dict[str, CouncilMember] = {}
        self._treasury_balance: float = 1_000_000_000  # 1B VRS initial treasury
        self._treasury_disbursed: float = 0
        self._lock = threading.Lock()

    # === Proposals ===

    def create_proposal(
        self, type: str, title: str, description: str, proposer: str,
        proposal_data: dict = None, voting_period_days: int = None,
        threshold: float = 0.5, block_height: int = 0,
    ) -> Proposal:
        """Create a new governance proposal."""
        proposal_id = f"prop-{secrets.token_hex(8)}"
        vp_days = voting_period_days or self._voting_period_days
        now = datetime.utcnow()
        voting_end = now + timedelta(days=vp_days)

        proposal = Proposal(
            id=proposal_id, type=type, title=title, description=description,
            proposer=proposer, voting_start=now.isoformat(),
            voting_end=voting_end.isoformat(),
            threshold=threshold, proposal_data=proposal_data or {},
            block_height=block_height,
        )

        # Auto-activate
        proposal.status = ProposalStatus.ACTIVE.value

        with self._lock:
            self._proposals[proposal_id] = proposal
            if proposer in self._council:
                self._council[proposer].proposals_created += 1

        logger.info("proposal_created", id=proposal_id, type=type, proposer=proposer)
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        return self._proposals.get(proposal_id)

    def list_proposals(
        self, status: str = None, type: str = None,
        proposer: str = None, limit: int = 50,
    ) -> list[Proposal]:
        proposals = list(self._proposals.values())
        if status:
            proposals = [p for p in proposals if p.status == status]
        if type:
            proposals = [p for p in proposals if p.type == type]
        if proposer:
            proposals = [p for p in proposals if p.proposer == proposer]
        proposals.sort(key=lambda p: p.created, reverse=True)
        return proposals[:limit]

    def cancel_proposal(self, proposal_id: str, canceller: str) -> bool:
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.ACTIVE.value:
            return False
        if proposal.proposer != canceller:
            return False
        proposal.status = ProposalStatus.CANCELLED.value
        return True

    def vote(self, proposal_id: str, voter: str, vote_type: str,
             voting_power: float = 1.0, reason: str = "") -> Optional[Vote]:
        """Cast a vote on a proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return None
        if proposal.status != ProposalStatus.ACTIVE.value:
            return None
        if datetime.utcnow() > datetime.fromisoformat(proposal.voting_end):
            proposal.status = ProposalStatus.EXPIRED.value
            return None

        # Check if already voted
        existing = [v for v in self._votes[proposal_id] if v.voter == voter]
        if existing:
            return None  # Can't vote twice

        vote = Vote(
            proposal_id=proposal_id, voter=voter, vote_type=vote_type,
            voting_power=voting_power, reason=reason,
        )
        self._votes[proposal_id].append(vote)

        # Update vote counts
        if vote_type == VoteType.AYE.value:
            proposal.aye_votes += voting_power
        elif vote_type == VoteType.NAY.value:
            proposal.nay_votes += voting_power
        else:
            proposal.abstain_votes += voting_power
        proposal.total_voters += 1

        if voter in self._council:
            self._council[voter].votes_cast += 1

        logger.info("vote_cast", proposal_id=proposal_id, voter=voter, vote=vote_type)
        return vote

    def tally_votes(self, proposal_id: str) -> dict:
        """Get vote tally for a proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {}

        total = proposal.aye_votes + proposal.nay_votes
        if total == 0:
            return {"aye_pct": 0, "nay_pct": 0, "abstain_pct": 0, "passes": False}

        aye_pct = (proposal.aye_votes / total) * 100
        nay_pct = (proposal.nay_votes / total) * 100
        abstain_pct = (proposal.abstain_votes / max(1, total + proposal.abstain_votes)) * 100
        passes = aye_pct >= proposal.threshold * 100

        return {
            "aye": proposal.aye_votes,
            "nay": proposal.nay_votes,
            "abstain": proposal.abstain_votes,
            "total": total,
            "aye_pct": round(aye_pct, 2),
            "nay_pct": round(nay_pct, 2),
            "abstain_pct": round(abstain_pct, 2),
            "threshold_pct": proposal.threshold * 100,
            "passes": passes,
        }

    def finalize_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Finalize a proposal after voting ends."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.ACTIVE.value:
            return None

        # Check if voting ended
        if datetime.utcnow() <= datetime.fromisoformat(proposal.voting_end):
            return None

        tally = self.tally_votes(proposal_id)
        if tally.get("passes", False):
            proposal.status = ProposalStatus.PASSED.value
        else:
            proposal.status = ProposalStatus.REJECTED.value

        return proposal

    def execute_proposal(self, proposal_id: str, execution_hash: str = "") -> Optional[Proposal]:
        """Execute a passed proposal."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or proposal.status != ProposalStatus.PASSED.value:
            return None
        proposal.status = ProposalStatus.EXECUTED.value
        proposal.execution_hash = execution_hash
        proposal.executed_at = datetime.utcnow().isoformat()
        return proposal

    def get_votes(self, proposal_id: str) -> list[Vote]:
        return self._votes.get(proposal_id, [])

    def get_proposal_stats(self) -> dict:
        return {
            "total": len(self._proposals),
            "active": sum(1 for p in self._proposals.values() if p.status == "active"),
            "passed": sum(1 for p in self._proposals.values() if p.status == "passed"),
            "rejected": sum(1 for p in self._proposals.values() if p.status == "rejected"),
            "executed": sum(1 for p in self._proposals.values() if p.status == "executed"),
            "cancelled": sum(1 for p in self._proposals.values() if p.status == "cancelled"),
            "expired": sum(1 for p in self._proposals.values() if p.status == "expired"),
        }

    # === Treasury ===

    def create_treasury_proposal(
        self, title: str, description: str, proposer: str,
        beneficiary: str, amount: float, currency: str = "VRS",
        category: str = "general", threshold: int = 3,
        expires_days: int = 30, metadata: dict = None,
    ) -> TreasuryProposal:
        """Create a treasury spend proposal."""
        if amount > self._treasury_balance:
            raise ValueError("Amount exceeds treasury balance")

        proposal_id = f"tr-{secrets.token_hex(8)}"
        expires = datetime.utcnow() + timedelta(days=expires_days)

        proposal = TreasuryProposal(
            id=proposal_id, title=title, description=description,
            proposer=proposer, beneficiary=beneficiary, amount=amount,
            currency=currency, category=category, threshold=threshold,
            expires_at=expires.isoformat(), metadata=metadata or {},
        )
        self._treasury_proposals[proposal_id] = proposal
        logger.info("treasury_proposal_created", id=proposal_id, amount=amount)
        return proposal

    def approve_treasury_proposal(self, proposal_id: str, approver: str) -> Optional[TreasuryProposal]:
        """Council member approves a treasury proposal."""
        proposal = self._treasury_proposals.get(proposal_id)
        if not proposal or proposal.status != TreasuryStatus.PENDING.value:
            return None

        proposal.approvals += 1

        if proposal.approvals >= proposal.threshold:
            proposal.status = TreasuryStatus.APPROVED.value
            self._treasury_balance -= proposal.amount
            self._treasury_disbursed += proposal.amount

        return proposal

    def reject_treasury_proposal(self, proposal_id: str) -> Optional[TreasuryProposal]:
        """Reject a treasury proposal."""
        proposal = self._treasury_proposals.get(proposal_id)
        if not proposal or proposal.status != TreasuryStatus.PENDING.value:
            return None
        proposal.status = TreasuryStatus.REJECTED.value
        return proposal

    def disburse_treasury(self, proposal_id: str, tx_hash: str) -> Optional[TreasuryProposal]:
        """Mark a treasury proposal as disbursed."""
        proposal = self._treasury_proposals.get(proposal_id)
        if not proposal or proposal.status != TreasuryStatus.APPROVED.value:
            return None
        proposal.status = TreasuryStatus.DISBURSED.value
        proposal.disbursement_tx = tx_hash
        proposal.disbursement_date = datetime.utcnow().isoformat()
        return proposal

    def get_treasury_proposal(self, proposal_id: str) -> Optional[TreasuryProposal]:
        return self._treasury_proposals.get(proposal_id)

    def list_treasury_proposals(
        self, status: str = None, category: str = None,
        limit: int = 50,
    ) -> list[TreasuryProposal]:
        proposals = list(self._treasury_proposals.values())
        if status:
            proposals = [p for p in proposals if p.status == status]
        if category:
            proposals = [p for p in proposals if p.category == category]
        proposals.sort(key=lambda p: p.created, reverse=True)
        return proposals[:limit]

    def get_treasury_balance(self) -> dict:
        return {
            "balance": self._treasury_balance,
            "disbursed": self._treasury_disbursed,
            "pending": sum(p.amount for p in self._treasury_proposals.values()
                          if p.status == TreasuryStatus.PENDING.value),
            "approved_unpaid": sum(p.amount for p in self._treasury_proposals.values()
                                 if p.status == TreasuryStatus.APPROVED.value),
            "currency": "VRS",
        }

    def get_treasury_stats(self) -> dict:
        by_status = defaultdict(int)
        by_category = defaultdict(float)
        for p in self._treasury_proposals.values():
            by_status[p.status] += 1
            if p.status == TreasuryStatus.DISBURSED.value:
                by_category[p.category] += p.amount

        return {
            "total_proposals": len(self._treasury_proposals),
            "by_status": dict(by_status),
            "disbursed_by_category": dict(by_category),
            "total_disbursed": self._treasury_disbursed,
            "remaining_balance": self._treasury_balance,
        }

    # === Council ===

    def add_council_member(self, address: str, name: str, term_days: int = 365) -> CouncilMember:
        """Add a council member."""
        term_end = datetime.utcnow() + timedelta(days=term_days)
        member = CouncilMember(address=address, name=name, term_end=term_end.isoformat())
        self._council[address] = member
        logger.info("council_member_added", address=address, name=name)
        return member

    def remove_council_member(self, address: str) -> bool:
        if address in self._council:
            self._council[address].active = False
            return True
        return False

    def get_council_member(self, address: str) -> Optional[CouncilMember]:
        return self._council.get(address)

    def list_council_members(self, active_only: bool = True) -> list[CouncilMember]:
        members = list(self._council.values())
        if active_only:
            members = [m for m in members if m.active]
        return members

    def get_council_stats(self) -> dict:
        return {
            "total_members": len(self._council),
            "active_members": sum(1 for m in self._council.values() if m.active),
            "total_votes_cast": sum(m.votes_cast for m in self._council.values()),
            "total_proposals_created": sum(m.proposals_created for m in self._council.values()),
        }

    # === Overall Stats ===

    def get_dashboard(self) -> dict:
        return {
            "proposals": self.get_proposal_stats(),
            "treasury": self.get_treasury_balance(),
            "treasury_stats": self.get_treasury_stats(),
            "council": self.get_council_stats(),
            "active_proposals": [p.to_dict() for p in self.list_proposals(status="active", limit=5)],
            "recent_treasury": [t.to_dict() for t in self.list_treasury_proposals(limit=5)],
            "council_members": len(self.list_council_members()),
        }


_service: Optional[GovernanceService] = None

def get_governance_service() -> GovernanceService:
    global _service
    if _service is None:
        _service = GovernanceService()
    return _service
