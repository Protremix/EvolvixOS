"""API for NFT Marketplace — Phase 45."""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.models.user import User
from app.services.nft_marketplace import get_nft_marketplace_service

router = APIRouter(prefix="/nft", tags=["nft-marketplace"])


class CreateCollectionRequest(BaseModel):
    name: str
    description: str
    creator: str
    collection_type: str = "collectible"
    standard: str = "vrc-721"
    max_supply: int = 10000
    mint_price: float = 0.0
    royalty_bps: int = 250
    image: str = ""
    metadata_uri: str = ""
    tags: list = []


class MintNFTRequest(BaseModel):
    collection_id: str
    to_address: str
    name: str
    description: str = ""
    image: str = ""
    metadata_uri: str = ""
    attributes: dict = {}


class CreateListingRequest(BaseModel):
    nft_id: str
    seller: str
    price: float
    listing_type: str = "fixed_price"
    currency: str = "VRS"
    expires_days: int = 30


class PlaceBidRequest(BaseModel):
    bidder: str
    amount: float


@router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_active_user)):
    return get_nft_marketplace_service().get_dashboard()

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_active_user)):
    return get_nft_marketplace_service().get_stats()

# === Collections ===

@router.get("/collections")
async def list_collections(collection_type: Optional[str] = None, verified: Optional[bool] = None,
                            sort_by: str = "total_volume", limit: int = 50,
                            current_user: User = Depends(get_current_active_user)):
    return [c.to_dict() for c in get_nft_marketplace_service().list_collections(collection_type, verified, sort_by, limit)]

@router.post("/collections")
async def create_collection(req: CreateCollectionRequest, current_user: User = Depends(get_current_active_user)):
    return get_nft_marketplace_service().create_collection(
        req.name, req.description, req.creator, req.collection_type,
        req.standard, req.max_supply, req.mint_price, req.royalty_bps,
        req.image, req.metadata_uri, req.tags,
    ).to_dict()

@router.get("/collections/{collection_id}")
async def get_collection(collection_id: str, current_user: User = Depends(get_current_active_user)):
    c = get_nft_marketplace_service().get_collection(collection_id)
    return c.to_dict() if c else {"error": "Collection not found"}

@router.get("/collections/{collection_id}/stats")
async def collection_stats(collection_id: str, current_user: User = Depends(get_current_active_user)):
    s = get_nft_marketplace_service().get_collection_stats(collection_id)
    return s if s else {"error": "Collection not found"}

# === NFTs ===

@router.post("/mint")
async def mint_nft(req: MintNFTRequest, current_user: User = Depends(get_current_active_user)):
    nft = get_nft_marketplace_service().mint_nft(
        req.collection_id, req.to_address, req.name, req.description,
        req.image, req.metadata_uri, req.attributes,
    )
    return nft.to_dict() if nft else {"error": "Cannot mint (collection not found or max supply reached)"}

@router.get("/nfts")
async def list_nfts(collection_id: Optional[str] = None, owner: Optional[str] = None,
                    listed: Optional[bool] = None, sort_by: str = "minted_at", limit: int = 50,
                    current_user: User = Depends(get_current_active_user)):
    return [n.to_dict() for n in get_nft_marketplace_service().list_nfts(collection_id, owner, listed, limit, sort_by)]

@router.get("/nfts/{nft_id}")
async def get_nft(nft_id: str, current_user: User = Depends(get_current_active_user)):
    n = get_nft_marketplace_service().get_nft(nft_id)
    return n.to_dict() if n else {"error": "NFT not found"}

# === Listings ===

@router.post("/listings")
async def create_listing(req: CreateListingRequest, current_user: User = Depends(get_current_active_user)):
    l = get_nft_marketplace_service().create_listing(
        req.nft_id, req.seller, req.price, req.listing_type, req.currency, req.expires_days,
    )
    return l.to_dict() if l else {"error": "Cannot create listing"}

@router.get("/listings")
async def list_listings(collection_id: Optional[str] = None, listing_type: Optional[str] = None,
                         status: Optional[str] = None, seller: Optional[str] = None,
                         min_price: Optional[float] = None, max_price: Optional[float] = None,
                         sort_by: str = "price", limit: int = 50,
                         current_user: User = Depends(get_current_active_user)):
    return [l.to_dict() for l in get_nft_marketplace_service().list_listings(
        collection_id, listing_type, status, seller, min_price, max_price, sort_by, limit)]

@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str, current_user: User = Depends(get_current_active_user)):
    l = get_nft_marketplace_service().get_listing(listing_id)
    return l.to_dict() if l else {"error": "Listing not found"}

@router.delete("/listings/{listing_id}")
async def cancel_listing(listing_id: str, current_user: User = Depends(get_current_active_user)):
    l = get_nft_marketplace_service().cancel_listing(listing_id)
    return l.to_dict() if l else {"error": "Cannot cancel listing"}

@router.post("/listings/{listing_id}/buy")
async def buy_nft(listing_id: str, buyer: str, current_user: User = Depends(get_current_active_user)):
    result = get_nft_marketplace_service().buy_nft(listing_id, buyer)
    return result if result else {"error": "Cannot buy (listing not available)"}

@router.post("/listings/{listing_id}/view")
async def view_listing(listing_id: str, current_user: User = Depends(get_current_active_user)):
    get_nft_marketplace_service().increment_views(listing_id)
    return {"viewed": True}

# === Auctions ===

@router.post("/listings/{listing_id}/bids")
async def place_bid(listing_id: str, req: PlaceBidRequest, current_user: User = Depends(get_current_active_user)):
    b = get_nft_marketplace_service().place_bid(listing_id, req.bidder, req.amount)
    return b.to_dict() if b else {"error": "Cannot place bid (must be higher than current bid)"}

@router.get("/listings/{listing_id}/bids")
async def list_bids(listing_id: str, current_user: User = Depends(get_current_active_user)):
    return [b.to_dict() for b in get_nft_marketplace_service().list_bids(listing_id)]

@router.post("/listings/{listing_id}/end-auction")
async def end_auction(listing_id: str, current_user: User = Depends(get_current_active_user)):
    result = get_nft_marketplace_service().end_auction(listing_id)
    return result if result else {"error": "Cannot end auction"}

# === Transfers ===

@router.post("/nfts/{nft_id}/transfer")
async def transfer_nft(nft_id: str, from_address: str, to_address: str,
                         current_user: User = Depends(get_current_active_user)):
    n = get_nft_marketplace_service().transfer_nft(nft_id, from_address, to_address)
    return n.to_dict() if n else {"error": "Cannot transfer"}

@router.get("/transfers")
async def list_transfers(nft_id: Optional[str] = None, collection_id: Optional[str] = None,
                          limit: int = 50, current_user: User = Depends(get_current_active_user)):
    return [t.to_dict() for t in get_nft_marketplace_service().list_transfers(nft_id, collection_id, limit)]

# === Favorites ===

@router.post("/favorites/{nft_id}")
async def toggle_favorite(nft_id: str, user: str, current_user: User = Depends(get_current_active_user)):
    is_fav = get_nft_marketplace_service().toggle_favorite(user, nft_id)
    return {"favorited": is_fav}

@router.get("/favorites")
async def get_favorites(user: str, current_user: User = Depends(get_current_active_user)):
    return get_nft_marketplace_service().get_favorites(user)

# === Monitoring ===

@router.post("/monitoring/start")
async def start_monitoring(interval: int = 60, current_user: User = Depends(get_current_active_user)):
    get_nft_marketplace_service().start_monitoring(interval)
    return {"monitoring": True}

@router.post("/monitoring/stop")
async def stop_monitoring(current_user: User = Depends(get_current_active_user)):
    get_nft_marketplace_service().stop_monitoring()
    return {"monitoring": False}

@router.get("/monitoring/status")
async def monitoring_status(current_user: User = Depends(get_current_active_user)):
    return {"monitoring": get_nft_marketplace_service().is_monitoring()}
