"""
EvolvixOS-Verdis Blockchain Integration API.

Provides comprehensive access to the Verdis blockchain data from EvolvixOS,
including chain state, validators, DEX pools, carbon credits, governance,
staking, and tokenomics.
"""

import logging
from fastapi import APIRouter, HTTPException, Query

from app.integrations.verdis_enhanced import verdis_enhanced

logger = logging.getLogger("evolvixos")
router = APIRouter(prefix="/verdis", tags=["Verdis Blockchain"])


@router.get("/dashboard")
async def get_verdis_dashboard():
    """Get a comprehensive dashboard of all Verdis blockchain metrics."""
    return verdis_enhanced.get_dashboard()


@router.get("/chain-state")
async def get_chain_state():
    """Get current chain state (health, properties, runtime version)."""
    state = verdis_enhanced.get_chain_state()
    if not state.get("connected"):
        raise HTTPException(status_code=503, detail="Verdis blockchain is not reachable")
    return state


@router.get("/blocks/latest")
async def get_latest_blocks(
    count: int = Query(default=10, ge=1, le=50, description="Number of blocks to return")
):
    """Get the latest N blocks from the chain."""
    return verdis_enhanced.get_latest_blocks(count)


@router.get("/blocks/{block_number}")
async def get_block(block_number: int):
    """Get a specific block by number."""
    if block_number < 0:
        raise HTTPException(status_code=400, detail="Block number must be non-negative")
    block = verdis_enhanced.get_block_by_number(block_number)
    if not block:
        raise HTTPException(status_code=404, detail=f"Block #{block_number} not found")
    return block


@router.get("/validators/list")
async def get_validators():
    """Get all active validators with details."""
    return verdis_enhanced.get_validators()


@router.get("/validators/stats")
async def get_validator_stats():
    """Get validator statistics (count, avg green score, total stake)."""
    return verdis_enhanced.get_validator_count()


@router.get("/dex/pools")
async def get_dex_pools():
    """Get all AMM DEX pools."""
    return verdis_enhanced.get_dex_pools()


@router.get("/dex/stats")
async def get_dex_stats():
    """Get DEX statistics (pool count, total liquidity, volume)."""
    return verdis_enhanced.get_dex_stats()


@router.get("/eco/stats")
async def get_eco_stats():
    """Get ecological impact statistics (carbon credits, trees, green validators)."""
    return verdis_enhanced.get_eco_stats()


@router.get("/eco/carbon-credits")
async def get_carbon_credits(
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get carbon credit entries."""
    return verdis_enhanced.get_carbon_credits(limit)


@router.get("/governance/proposals")
async def get_governance_proposals():
    """Get active governance proposals."""
    return verdis_enhanced.get_governance_proposals()


@router.get("/governance/treasury")
async def get_treasury_balance():
    """Get treasury balance and spending info."""
    return verdis_enhanced.get_treasury_balance()


@router.get("/tokenomics")
async def get_tokenomics():
    """Get token economics data (supply, staking, APY)."""
    return verdis_enhanced.get_tokenomics()


@router.get("/tokenomics/allocation")
async def get_allocation():
    """Get token allocation breakdown by category."""
    return verdis_enhanced.get_allocation()


@router.get("/staking")
async def get_staking_info():
    """Get staking information (APY, unbonding period, min stake)."""
    return verdis_enhanced.get_staking_info()


@router.get("/blockchain-health")
async def get_blockchain_health():
    """Get blockchain health check (for monitoring)."""
    state = verdis_enhanced.get_chain_state()
    return {
        "connected": state.get("connected", False),
        "peers": state.get("health", {}).get("peers", 0),
        "is_syncing": state.get("health", {}).get("isSyncing", False),
        "block_height": int(state.get("header", {}).get("number", "0x0"), 16) if state.get("header") else 0,
        "spec_version": state.get("runtime_version", {}).get("specVersion", 0),
    }
