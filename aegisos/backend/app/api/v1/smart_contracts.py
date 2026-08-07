"""API for Smart Contract Tools — Phase 33."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.smart_contracts import get_smart_contract_service

router = APIRouter(prefix="/smart-contracts", tags=["smart-contracts"])


class ScanRequest(BaseModel):
    source_code: str
    contract_name: str = "unnamed"


class RegisterContractRequest(BaseModel):
    name: str
    address: str
    deployer: str
    category: str
    compiler_version: str = "0.8.20"
    abi: str = "[]"
    source_code: str = ""
    network: str = "verdis-mainnet"
    block_number: int = 0
    tx_hash: str = ""
    metadata: dict = {}


class VerifyContractRequest(BaseModel):
    source_code: str


@router.get("/templates")
async def list_templates(category: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_smart_contract_service().list_templates(category)]

@router.get("/templates/{template_id}")
async def get_template(template_id: str, current_user: User = Depends(get_current_active_user)):
    t = get_smart_contract_service().get_template(template_id)
    return t.to_dict() if t else {"error": "Template not found"}

@router.get("/categories")
async def list_categories():
    return get_smart_contract_service().list_categories()

@router.post("/scan")
async def scan_contract(req: ScanRequest, current_user: User = Depends(get_current_active_user)):
    return get_smart_contract_service().scan_contract(req.source_code, req.contract_name).to_dict()

@router.get("/scan/{scan_id}")
async def get_scan(scan_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_smart_contract_service().get_scan(scan_id)
    return s.to_dict() if s else {"error": "Scan not found"}

@router.get("/scans")
async def list_scans(limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [s.to_dict() for s in get_smart_contract_service().list_scans(limit)]

@router.post("/register")
async def register_contract(req: RegisterContractRequest, current_user: User = Depends(get_current_active_user)):
    return get_smart_contract_service().register_contract(
        req.name, req.address, req.deployer, req.category,
        req.compiler_version, req.abi, req.source_code,
        req.network, req.block_number, req.tx_hash, req.metadata,
    ).to_dict()

@router.post("/contract/{contract_id}/verify")
async def verify_contract(contract_id: str, req: VerifyContractRequest, current_user: User = Depends(get_current_active_user)):
    result = get_smart_contract_service().verify_contract(contract_id, req.source_code)
    return result.to_dict() if result else {"error": "Contract not found"}

@router.get("/contract/{contract_id}")
async def get_contract(contract_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_smart_contract_service().get_contract(contract_id)
    return c.to_dict() if c else {"error": "Contract not found"}

@router.get("/contract/address/{address}")
async def get_contract_by_address(address: str, current_user: User = Depends(get_current_active_user)):
    c = get_smart_contract_service().get_contract_by_address(address)
    return c.to_dict() if c else {"error": "Contract not found"}

@router.get("/contracts")
async def list_contracts(category: Optional[str] = None, deployer: Optional[str] = None, verified: Optional[bool] = None, limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_smart_contract_service().list_contracts(category, deployer, verified, limit)]

@router.post("/contract/{contract_id}/deprecate")
async def deprecate_contract(contract_id: str, current_user: User = Depends(get_current_active_user)):
    return {"deprecated": get_smart_contract_service().deprecate_contract(contract_id)}

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_smart_contract_service().get_stats()
