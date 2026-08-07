"""API for Tokenomics Dashboard — Phase 36."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.tokenomics import get_tokenomics_service, FlowType

router = APIRouter(prefix="/tokenomics", tags=["tokenomics"])


class CreateVestingRequest(BaseModel):
    beneficiary: str
    allocation_type: str
    total_amount: float
    vesting_months: int
    cliff_months: int = 0


class RecordFlowRequest(BaseModel):
    flow_type: str
    from_addr: str
    to_addr: str
    amount: float
    block_height: int = 0
    tx_hash: str = ""


class UpdateUtilityRequest(BaseModel):
    staked_amount: Optional[float] = None
    governance_locked: Optional[float] = None
    treasury_balance: Optional[float] = None
    liquidity_pools: Optional[float] = None
    burned: Optional[float] = None
    transaction_fees: Optional[float] = None


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_dashboard()

@router.get("/supply")
async def get_supply(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_circulating_supply()

@router.get("/allocations")
async def get_allocations(current_user: User = Depends(get_current_active_user)):
    return [a.to_dict() for a in get_tokenomics_service().get_allocations()]

@router.get("/allocations/{alloc_type}")
async def get_allocation(alloc_type: str, current_user: User = Depends(get_current_active_user)):
    a = get_tokenomics_service().get_allocation(alloc_type)
    return a.to_dict() if a else {"error": "Allocation not found"}

@router.post("/vesting")
async def create_vesting(req: CreateVestingRequest, current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().create_vesting_schedule(
        req.beneficiary, req.allocation_type, req.total_amount,
        req.vesting_months, req.cliff_months,
    ).to_dict()

@router.get("/vesting")
async def list_vesting(beneficiary: Optional[str] = None, status: Optional[str] = None,
                       current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_tokenomics_service().list_vesting_schedules(beneficiary, status)]

@router.get("/vesting/{schedule_id}")
async def get_vesting(schedule_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_tokenomics_service().get_vesting_schedule(schedule_id)
    return s.to_dict() if s else {"error": "Schedule not found"}

@router.post("/vesting/{schedule_id}/release")
async def release_vesting(schedule_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_tokenomics_service().release_vested(schedule_id)
    return s.to_dict() if s else {"error": "Schedule not found"}

@router.get("/vesting/stats")
async def vesting_stats(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_vesting_stats()

@router.post("/flows")
async def record_flow(req: RecordFlowRequest, current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().record_flow(
        req.flow_type, req.from_addr, req.to_addr, req.amount, req.block_height, req.tx_hash,
    ).to_dict()

@router.get("/flows")
async def list_flows(flow_type: Optional[str] = None, limit: int = 50,
                     from_addr: Optional[str] = None, to_addr: Optional[str] = None,
                     current_user: User = Depends(get_current_active_user)):
    return [f.to_dict() for f in get_tokenomics_service().list_flows(flow_type, limit, from_addr, to_addr)]

@router.get("/flows/stats")
async def flow_stats(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_flow_stats()

@router.get("/utility")
async def get_utility(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_utility().to_dict()

@router.patch("/utility")
async def update_utility(req: UpdateUtilityRequest, current_user: User = Depends(get_current_active_user)):
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    return get_tokenomics_service().update_utility(**kwargs).to_dict()

@router.get("/distribution/chart")
async def distribution_chart(current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_token_distribution_chart()

@router.get("/supply/progression")
async def supply_progression(months: int = 12, current_user: User = Depends(get_current_active_user)):
    return get_tokenomics_service().get_supply_progression(months)

@router.get("/flow-types")
async def get_flow_types():
    return [{"value": f.value, "name": f.value.replace("_", " ").title()} for f in FlowType]
