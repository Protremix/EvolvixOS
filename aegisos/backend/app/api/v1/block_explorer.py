"""API for Block Explorer — Phase 47."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.block_explorer import get_block_explorer_service

router = APIRouter(prefix="/explorer", tags=["block-explorer"])


class SearchRequest(BaseModel):
    query: str


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_block_explorer_service().get_dashboard()

@router.get("/stats")
async def get_network_stats(current_user: User = Depends(get_current_active_user)):
    return get_block_explorer_service().get_network_stats()

# === Blocks ===

@router.get("/blocks")
async def list_blocks(limit: int = 50, offset: int = 0,
                       current_user: User = Depends(get_current_active_user)):
    return [b.to_dict() for b in get_block_explorer_service().list_blocks(limit, offset)]

@router.get("/blocks/latest")
async def latest_blocks(limit: int = 20, current_user: User = Depends(get_current_active_user)):
    return [b.to_dict() for b in get_block_explorer_service().get_latest_blocks(limit)]

@router.get("/blocks/{height}")
async def get_block(height: int, current_user: User = Depends(get_current_active_user)):
    b = get_block_explorer_service().get_block(height=height)
    return b.to_dict() if b else {"error": "Block not found"}

@router.get("/blocks/{height}/transactions")
async def block_transactions(height: int, limit: int = 50,
                              current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_block_explorer_service().get_block_transactions(height, limit)]

@router.get("/blocks/hash/{block_hash}")
async def get_block_by_hash(block_hash: str, current_user: User = Depends(get_current_active_user)):
    b = get_block_explorer_service().get_block(block_hash=block_hash)
    return b.to_dict() if b else {"error": "Block not found"}

# === Transactions ===

@router.get("/transactions")
async def list_transactions(address: Optional[str] = None, tx_type: Optional[str] = None,
                              status: Optional[str] = None, limit: int = 50, offset: int = 0,
                              sort_by: str = "timestamp",
                              current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_block_explorer_service().list_transactions(
        address, tx_type, status, limit, offset, sort_by)]

@router.get("/transactions/{tx_hash}")
async def get_transaction(tx_hash: str, current_user: User = Depends(get_current_active_user)):
    t = get_block_explorer_service().get_transaction(tx_hash)
    return t.to_dict() if t else {"error": "Transaction not found"}

# === Addresses ===

@router.get("/addresses/{address}")
async def get_address(address: str, current_user: User = Depends(get_current_active_user)):
    a = get_block_explorer_service().get_address(address)
    return a.to_dict() if a else {"error": "Address not found"}

@router.get("/addresses/{address}/transactions")
async def address_transactions(address: str, limit: int = 50, offset: int = 0,
                                 current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_block_explorer_service().get_address_transactions(address, limit, offset)]

@router.get("/addresses")
async def top_addresses(sort_by: str = "balance", limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [a.to_dict() for a in get_block_explorer_service().list_top_addresses(sort_by, limit)]

# === Contracts ===

@router.get("/contracts")
async def list_contracts(verified: Optional[bool] = None, standard: Optional[str] = None,
                          limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_block_explorer_service().list_contracts(verified, standard, limit)]

@router.get("/contracts/{address}")
async def get_contract(address: str, current_user: User = Depends(get_current_active_user)):
    c = get_block_explorer_service().get_contract(address)
    return c.to_dict() if c else {"error": "Contract not found"}

# === Event Logs ===

@router.get("/logs")
async def list_logs(address: Optional[str] = None, tx_hash: Optional[str] = None,
                     block_height: Optional[int] = None, topic0: Optional[str] = None,
                     limit: int = 100, offset: int = 0,
                     current_user: User = Depends(get_current_active_user)):
    return [l.to_dict() for l in get_block_explorer_service().list_logs(
        address, tx_hash, block_height, topic0, limit, offset)]

# === Search ===

@router.get("/search")
async def search(query: str, current_user: User = Depends(get_current_active_user)):
    return get_block_explorer_service().search(query)

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 6, current_user: User = Depends(get_current_active_user)):
    get_block_explorer_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_block_explorer_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_block_explorer_service().is_monitoring()}
