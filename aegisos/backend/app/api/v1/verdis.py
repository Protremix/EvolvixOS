"""
Verdis Blockchain API endpoints.

Provides REST access to the Verdis blockchain integration for the
EvolvixOS dashboard and AI agents.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/verdis", tags=["verdis-blockchain"])


class ChainHealthResponse(BaseModel):
    connected: bool
    chain: str = "Verdis"
    token_symbol: str = "VRDX"
    block_height: str = ""
    peers: int = 0
    is_syncing: bool = False
    spec_version: int = 0
    active_validators: int = 0


class NetworkInfoResponse(BaseModel):
    chain: str = "Verdis"
    consensus: str = "BABE/GRANDPA + DPoS"
    node_name: str = ""
    node_version: str = ""
    rpc_method_count: int = 0


@router.get("/health", response_model=ChainHealthResponse)
async def get_chain_health(current_user: User = Depends(get_current_active_user)):
    """Get Verdis blockchain health metrics."""
    from app.integrations.verdis import verdis

    health = verdis.get_chain_health()
    validators = verdis.get_validators()

    return ChainHealthResponse(
        connected=health.get("connected", False),
        chain=health.get("chain_name", "Verdis"),
        token_symbol=health.get("token_symbol", "VRDX"),
        block_height=str(health.get("block_height", "")),
        peers=health.get("peers", 0),
        is_syncing=health.get("is_syncing", False),
        spec_version=health.get("spec_version", 0),
        active_validators=len(validators),
    )


@router.get("/network")
async def get_network_info(current_user: User = Depends(get_current_active_user)):
    """Get Verdis network information."""
    from app.integrations.verdis import verdis
    return verdis.get_network_info()


@router.get("/validators")
async def get_validators(current_user: User = Depends(get_current_active_user)):
    """Get active Verdis validators."""
    from app.integrations.verdis import verdis
    validators = verdis.get_validators()
    return {"count": len(validators), "validators": validators}


@router.get("/summary")
async def get_health_summary(current_user: User = Depends(get_current_active_user)):
    """Get a human-readable health summary for AI agents."""
    from app.integrations.verdis import verdis
    summary = verdis.get_health_summary()
    return {"summary": summary}
