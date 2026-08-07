"""
Cross-Server Bridge: EvolvixOS <-> Verdis Substrate Blockchain
Proxies RPC calls and provides a unified API for blockchain data.
"""
import httpx
import asyncio
from fastapi import APIRouter, Request, HTTPException, Response
from typing import Optional

router = APIRouter(prefix="/verdis-bridge", tags=["verdis-bridge"])

# Verdis Substrate RPC endpoint
VERDIS_RPC_URL = "https://verdischain.com/rpc"
VERDIS_WS_URL = "wss://verdischain.com/ws"
REQUEST_TIMEOUT = 10.0

# Cache for frequently accessed data
_cache = {}
_cache_ttl = 5  # seconds


async def rpc_call(method: str, params: list = None, timeout: float = REQUEST_TIMEOUT):
    """Make a JSON-RPC call to the Verdis Substrate node."""
    if params is None:
        params = []
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            VERDIS_RPC_URL,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            headers={"Content-Type": "application/json"},
        )
        data = resp.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=f"RPC Error: {data[error]}")
        return data.get("result")


async def cached_rpc_call(method: str, params: list = None, ttl: int = _cache_ttl):
    """Cached RPC call for frequently accessed data."""
    import time
    key = f"{method}:{params}"
    now = time.time()
    if key in _cache and (now - _cache[key][1]) < ttl:
        return _cache[key][0]
    result = await rpc_call(method, params)
    _cache[key] = (result, now)
    return result


@router.get("/health")
async def bridge_health():
    """Check bridge connectivity to Verdis Substrate node."""
    try:
        health = await rpc_call("system_health")
        properties = await cached_rpc_call("system_properties")
        return {
            "status": "connected",
            "verdis_chain": {
                "peers": health.get("peers", 0),
                "is_syncing": health.get("isSyncing", False),
                "token_symbol": properties.get("tokenSymbol", "VRDX"),
                "token_decimals": properties.get("tokenDecimals", 9),
                "ss58_format": properties.get("ss58Format", 909),
            },
            "rpc_url": VERDIS_RPC_URL,
        }
    except Exception as e:
        return {"status": "disconnected", "error": str(e), "rpc_url": VERDIS_RPC_URL}


@router.post("/rpc")
async def proxy_rpc(request: Request):
    """Proxy any JSON-RPC call to the Verdis Substrate node."""
    body = await request.json()
    method = body.get("method")
    params = body.get("params", [])
    
    if not method:
        raise HTTPException(status_code=400, detail="Missing method in request")
    
    try:
        result = await rpc_call(method, params)
        return {"jsonrpc": "2.0", "id": body.get("id", 1), "result": result}
    except HTTPException:
        raise
    except Exception as e:
        return {"jsonrpc": "2.0", "id": body.get("id", 1), "error": {"code": -32603, "message": str(e)}}


@router.get("/chain/head")
async def get_chain_head():
    """Get the latest block header."""
    header = await cached_rpc_call("chain_getHeader", [])
    return header


@router.get("/chain/block/{block_number}")
async def get_block(block_number: str):
    """Get a specific block by hash or number."""
    if block_number.isdigit():
        block_hash = await rpc_call("chain_getBlockHash", [int(block_number)])
    else:
        block_hash = block_number
    block = await rpc_call("chain_getBlock", [block_hash])
    return block


@router.get("/chain/blocks/latest")
async def get_latest_blocks(limit: int = 10):
    """Get the latest N blocks."""
    header = await cached_rpc_call("chain_getHeader", [])
    block_num = int(header.get("number", "0"), 16)
    
    blocks = []
    for i in range(max(0, block_num - limit + 1), block_num + 1):
        try:
            block_hash = await rpc_call("chain_getBlockHash", [i])
            block_header = await rpc_call("chain_getHeader", [block_hash])
            blocks.append({
                "number": i,
                "hash": block_hash,
                "parent_hash": block_header.get("parentHash"),
                "state_root": block_header.get("stateRoot"),
                "extrinsics_root": block_header.get("extrinsicsRoot"),
            })
        except Exception:
            pass
    return {"blocks": blocks, "latest": block_num}


@router.get("/validators")
async def get_validators():
    """Get active validators from the Substrate chain."""
    validators = await cached_rpc_call("session_validators", [], ttl=30)
    return {"validators": validators}


@router.get("/system/info")
async def get_system_info():
    """Get system info from the Substrate node."""
    health = await cached_rpc_call("system_health", [], ttl=5)
    properties = await cached_rpc_call("system_properties", [], ttl=60)
    chain = await cached_rpc_call("system_chain", [], ttl=60)
    version = await cached_rpc_call("system_version", [], ttl=60)
    name = await cached_rpc_call("system_name", [], ttl=60)
    
    return {
        "chain_name": chain,
        "node_name": name,
        "node_version": version,
        "health": health,
        "properties": properties,
    }


@router.get("/dex/pools")
async def get_dex_pools():
    """Get all DEX pools from the AmmDex pallet."""
    try:
        count = await cached_rpc_call("amm_dex_getPoolCount", [], ttl=5)
        pools = []
        for i in range(count):
            pool = await rpc_call("amm_dex_getPool", [i])
            if pool:
                pools.append({"id": i, "data": pool})
        return {"pool_count": count, "pools": pools}
    except Exception as e:
        return {"pool_count": 0, "pools": [], "error": str(e)}


@router.get("/dex/prices")
async def get_dex_prices():
    """Get token prices from the AmmDex."""
    try:
        token_count = await cached_rpc_call("amm_dex_getTokenPoolCount", [], ttl=5)
        prices = []
        for i in range(token_count):
            price = await rpc_call("amm_dex_getPrice", [i])
            if price:
                prices.append({"token_id": i, "price": price})
        return {"prices": prices}
    except Exception as e:
        return {"prices": [], "error": str(e)}


@router.get("/account/{address}/balance")
async def get_account_balance(address: str):
    """Get account balance from the Substrate chain."""
    try:
        balance = await rpc_call("system_accountNextIndex", [address])
        return {"address": address, "nonce": balance}
    except Exception:
        # Try storage query
        try:
            storage = await rpc_call("state_getStorage", [
                "0x" + address.encode().hex()
            ])
            return {"address": address, "storage": storage}
        except Exception as e:
            return {"address": address, "error": str(e)}


@router.get("/methods")
async def list_rpc_methods():
    """List all available RPC methods."""
    methods = await cached_rpc_call("rpc_methods", [], ttl=300)
    return methods
