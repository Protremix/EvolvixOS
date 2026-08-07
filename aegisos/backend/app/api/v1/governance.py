"""API for Governance & Treasury — Phase 35."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.governance import get_governance_service, ProposalType, ProposalStatus, VoteType

router = APIRouter(prefix="/governance", tags=["governance"])


class CreateProposalRequest(BaseModel):
    type: str
    title: str
    description: str
    proposer: str
    proposal_data: dict = {}
    voting_period_days: int = 7
    threshold: float = 0.5
    block_height: int = 0


class VoteRequest(BaseModel):
    voter: str
    vote_type: str
    voting_power: float = 1.0
    reason: str = ""


class CreateTreasuryRequest(BaseModel):
    title: str
    description: str
    proposer: str
    beneficiary: str
    amount: float
    currency: str = "VRS"
    category: str = "general"
    threshold: int = 3
    expires_days: int = 30
    metadata: dict = {}


class AddCouncilMemberRequest(BaseModel):
    address: str
    name: str
    term_days: int = 365


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_governance_service().get_dashboard()

# === Proposals ===

@router.post("/proposals")
async def create_proposal(req: CreateProposalRequest, current_user: User = Depends(get_current_active_user)):
    return get_governance_service().create_proposal(
        req.type, req.title, req.description, req.proposer,
        req.proposal_data, req.voting_period_days, req.threshold, req.block_height,
    ).to_dict()

@router.get("/proposals")
async def list_proposals(status: Optional[str] = None, type: Optional[str] = None,
                         proposer: Optional[str] = None, limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [p.to_dict() for p in get_governance_service().list_proposals(status, type, proposer, limit)]

@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_governance_service().get_proposal(proposal_id)
    return p.to_dict() if p else {"error": "Proposal not found"}

@router.post("/proposals/{proposal_id}/vote")
async def vote(proposal_id: str, req: VoteRequest, current_user: User = Depends(get_current_active_user)):
    result = get_governance_service().vote(proposal_id, req.voter, req.vote_type, req.voting_power, req.reason)
    return result.to_dict() if result else {"error": "Cannot vote on this proposal"}

@router.get("/proposals/{proposal_id}/tally")
async def tally_votes(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    return get_governance_service().tally_votes(proposal_id)

@router.get("/proposals/{proposal_id}/votes")
async def get_votes(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    return [v.to_dict() for v in get_governance_service().get_votes(proposal_id)]

@router.post("/proposals/{proposal_id}/finalize")
async def finalize_proposal(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    p = get_governance_service().finalize_proposal(proposal_id)
    return p.to_dict() if p else {"error": "Cannot finalize"}

@router.post("/proposals/{proposal_id}/execute")
async def execute_proposal(proposal_id: str, execution_hash: str = "", current_user: User = Depends(get_current_active_user)):
    p = get_governance_service().execute_proposal(proposal_id, execution_hash)
    return p.to_dict() if p else {"error": "Cannot execute"}

@router.post("/proposals/{proposal_id}/cancel")
async def cancel_proposal(proposal_id: str, canceller: str = "", current_user: User = Depends(get_current_active_user)):
    return {"cancelled": get_governance_service().cancel_proposal(proposal_id, canceller)}

@router.get("/proposals/stats")
async def proposal_stats(current_user: User = Depends(get_current_active_user)):
    return get_governance_service().get_proposal_stats()

# === Treasury ===

@router.post("/treasury")
async def create_treasury_proposal(req: CreateTreasuryRequest, current_user: User = Depends(get_current_active_user)):
    try:
        return get_governance_service().create_treasury_proposal(
            req.title, req.description, req.proposer, req.beneficiary,
            req.amount, req.currency, req.category, req.threshold,
            req.expires_days, req.metadata,
        ).to_dict()
    except ValueError as e:
        return {"error": str(e)}

@router.get("/treasury")
async def list_treasury(status: Optional[str] = None, category: Optional[str] = None,
                        limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_governance_service().list_treasury_proposals(status, category, limit)]

@router.get("/treasury/{proposal_id}")
async def get_treasury_proposal(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_governance_service().get_treasury_proposal(proposal_id)
    return t.to_dict() if t else {"error": "Not found"}

@router.post("/treasury/{proposal_id}/approve")
async def approve_treasury(proposal_id: str, approver: str = "", current_user: User = Depends(get_current_active_user)):
    t = get_governance_service().approve_treasury_proposal(proposal_id, approver)
    return t.to_dict() if t else {"error": "Cannot approve"}

@router.post("/treasury/{proposal_id}/reject")
async def reject_treasury(proposal_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_governance_service().reject_treasury_proposal(proposal_id)
    return t.to_dict() if t else {"error": "Cannot reject"}

@router.post("/treasury/{proposal_id}/disburse")
async def disburse_treasury(proposal_id: str, tx_hash: str = "", current_user: User = Depends(get_current_active_user)):
    t = get_governance_service().disburse_treasury(proposal_id, tx_hash)
    return t.to_dict() if t else {"error": "Cannot disburse"}

@router.get("/treasury/balance")
async def treasury_balance(current_user: User = Depends(get_current_active_user)):
    return get_governance_service().get_treasury_balance()

@router.get("/treasury/stats")
async def treasury_stats(current_user: User = Depends(get_current_active_user)):
    return get_governance_service().get_treasury_stats()

# === Council ===

@router.post("/council/members")
async def add_council_member(req: AddCouncilMemberRequest, current_user: User = Depends(get_current_active_user)):
    return get_governance_service().add_council_member(req.address, req.name, req.term_days).to_dict()

@router.delete("/council/members/{address}")
async def remove_council_member(address: str, current_user: User = Depends(get_current_active_user)):
    return {"removed": get_governance_service().remove_council_member(address)}

@router.get("/council/members")
async def list_council_members(active_only: bool = True, current_user: User = Depends(get_current_active_user)):
    return [m.to_dict() for m in get_governance_service().list_council_members(active_only)]

@router.get("/council/members/{address}")
async def get_council_member(address: str, current_user: User = Depends(get_current_active_user)):
    m = get_governance_service().get_council_member(address)
    return m.to_dict() if m else {"error": "Not found"}

@router.get("/council/stats")
async def council_stats(current_user: User = Depends(get_current_active_user)):
    return get_governance_service().get_council_stats()

# === Types ===

@router.get("/types/proposals")
async def get_proposal_types():
    return [{"value": p.value, "name": p.value.replace("_", " ").title()} for p in ProposalType]

@router.get("/types/votes")
async def get_vote_types():
    return [{"value": v.value, "name": v.value.title()} for v in VoteType]
