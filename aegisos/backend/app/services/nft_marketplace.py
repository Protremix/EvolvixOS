"""
NFT Marketplace — Phase 45

NFT minting, listing, buying, selling, bidding, collections, and trading
on the Verdis blockchain with carbon credit and reforestation NFT support.
"""

import secrets
import time
import threading
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from app.core.logging import get_logger

logger = get_logger("service.nft_marketplace")


class NFTStandard(str, Enum):
    VRC721 = "vrc-721"
    VRC1155 = "vrc-1155"


class ListingType(str, Enum):
    FIXED = "fixed_price"
    AUCTION = "auction"
    BUNDLE = "bundle"


class ListingStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class AuctionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CollectionType(str, Enum):
    ART = "art"
    CARBON_CREDIT = "carbon_credit"
    REFORESTATION = "reforestation"
    GREEN_VALIDATOR = "green_validator"
    GAMING = "gaming"
    MUSIC = "music"
    DOMAIN = "domain"
    UTILITY = "utility"
    COLLECTIBLE = "collectible"


@dataclass
class NFTCollection:
    id: str
    name: str
    description: str
    creator: str
    collection_type: str = CollectionType.COLLECTIBLE.value
    standard: str = NFTStandard.VRC721.value
    total_supply: int = 0
    max_supply: int = 10000
    mint_price: float = 0.0
    royalty_bps: int = 250  # 2.5%
    verified: bool = False
    floor_price: float = 0.0
    total_volume: float = 0.0
    image: str = ""
    metadata_uri: str = ""
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NFTItem:
    id: str
    token_id: str
    collection_id: str
    collection_name: str
    owner: str
    creator: str
    name: str
    description: str = ""
    image: str = ""
    metadata_uri: str = ""
    attributes: dict = field(default_factory=dict)
    standard: str = NFTStandard.VRC721.value
    minted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_sale_price: float = 0.0
    last_sale_date: str = ""
    listed: bool = False
    transfer_count: int = 0
    royalty_paid: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Listing:
    id: str
    nft_id: str
    token_id: str
    collection_id: str
    collection_name: str
    seller: str
    listing_type: str = ListingType.FIXED.value
    price: float = 0.0
    currency: str = "VRS"
    status: str = ListingStatus.ACTIVE.value
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""
    buyer: str = ""
    sold_at: str = ""
    sold_price: float = 0.0
    views: int = 0
    favorites: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Bid:
    id: str
    listing_id: str
    nft_id: str
    bidder: str
    amount: float
    currency: str = "VRS"
    created: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "active"  # active, won, lost, cancelled
    expires_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NFTTransfer:
    id: str
    nft_id: str
    token_id: str
    collection_id: str
    from_address: str
    to_address: str
    price: float = 0.0
    currency: str = "VRS"
    tx_type: str = "sale"  # sale, transfer, mint, burn
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class NFTMarketplaceService:
    """NFT marketplace with minting, listings, auctions, and trading."""

    def __init__(self, max_history: int = 10000):
        self._collections: dict[str, NFTCollection] = {}
        self._nfts: dict[str, NFTItem] = {}
        self._listings: dict[str, Listing] = {}
        self._bids: dict[str, list[Bid]] = defaultdict(list)
        self._transfers: deque = deque(maxlen=max_history)
        self._favorites: dict[str, set] = defaultdict(set)  # user -> set of nft_ids
        self._lock = threading.Lock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._init_default_collections()
        self._init_sample_nfts()

    def _init_default_collections(self):
        """Initialize with default collections."""
        collections = [
            ("Verdis Carbon Credits", "Official carbon credit NFTs representing verified carbon offsets", CollectionType.CARBON_CREDIT.value, 10000, 100, 500),
            ("Green Earth Reforestation", "NFTs backed by real reforestation projects worldwide", CollectionType.REFORESTATION.value, 5000, 50, 1000),
            ("Eco Validators", "Commemorative NFTs for green validators on Verdis", CollectionType.GREEN_VALIDATOR.value, 101, 10, 50),
            ("Verdis Genesis Art", "Limited edition genesis art collection", CollectionType.ART.value, 500, 5, 250),
            ("Green Gaming Assets", "In-game eco-friendly digital assets", CollectionType.GAMING.value, 20000, 1, 100),
        ]
        for name, desc, ctype, max_supply, mint_price, royalty in collections:
            cid = f"col-{secrets.token_hex(8)}"
            self._collections[cid] = NFTCollection(
                id=cid, name=name, description=desc,
                creator="0xverdis", collection_type=ctype,
                max_supply=max_supply, mint_price=mint_price,
                royalty_bps=royalty * 10, verified=True,
            )

    def _init_sample_nfts(self):
        """Initialize with sample NFTs."""
        import random
        random.seed(42)

        collection_list = list(self._collections.values())
        for col in collection_list:
            num_nfts = min(random.randint(5, 20), col.max_supply)
            for i in range(num_nfts):
                token_id = str(random.randint(1, 999999))
                nft_id = f"nft-{secrets.token_hex(8)}"
                names = {
                    CollectionType.CARBON_CREDIT.value: [f"Carbon Credit #{i+1}", f"CO2 Offset #{i+1}", f"Green Credit #{i+1}"],
                    CollectionType.REFORESTATION.value: [f"Forest Plot #{i+1}", f"Tree Token #{i+1}", f"Reforest #{i+1}"],
                    CollectionType.GREEN_VALIDATOR.value: [f"Validator Badge #{i+1}", f"Green Node #{i+1}"],
                    CollectionType.ART.value: [f"Genesis Art #{i+1}", f"Verdis Vision #{i+1}"],
                    CollectionType.GAMING.value: [f"Eco Warrior #{i+1}", f"Green Shield #{i+1}"],
                }
                name = random.choice(names.get(col.collection_type, [f"NFT #{i+1}"]))

                nft = NFTItem(
                    id=nft_id, token_id=token_id, collection_id=col.id,
                    collection_name=col.name, owner=f"0x{secrets.token_hex(20)}",
                    creator=col.creator, name=name,
                    description=f"{name} from {col.name}",
                    attributes={"rarity": random.choice(["common", "uncommon", "rare", "epic", "legendary"]),
                               "score": random.randint(1, 100)},
                    last_sale_price=round(random.uniform(0, col.mint_price * 100), 2) if col.mint_price > 0 else 0,
                )
                self._nfts[nft_id] = nft
                col.total_supply += 1

                # Random listing
                if random.random() > 0.5:
                    listing_id = f"lst-{secrets.token_hex(8)}"
                    price = round(random.uniform(0.5, 500), 2)
                    listing = Listing(
                        id=listing_id, nft_id=nft_id, token_id=token_id,
                        collection_id=col.id, collection_name=col.name,
                        seller=nft.owner, price=price,
                        listing_type=random.choices([ListingType.FIXED.value, ListingType.AUCTION.value], weights=[70, 30])[0],
                    )
                    self._listings[listing_id] = listing
                    nft.listed = True
                    col.floor_price = min(col.floor_price or price, price) if price > 0 else col.floor_price

    # === Collections ===

    def create_collection(self, name: str, description: str, creator: str,
                          collection_type: str = CollectionType.COLLECTIBLE.value,
                          standard: str = NFTStandard.VRC721.value,
                          max_supply: int = 10000, mint_price: float = 0.0,
                          royalty_bps: int = 250, image: str = "",
                          metadata_uri: str = "", tags: list = None) -> NFTCollection:
        cid = f"col-{secrets.token_hex(8)}"
        collection = NFTCollection(
            id=cid, name=name, description=description, creator=creator,
            collection_type=collection_type, standard=standard,
            max_supply=max_supply, mint_price=mint_price,
            royalty_bps=royalty_bps, image=image, metadata_uri=metadata_uri,
            tags=tags or [],
        )
        self._collections[cid] = collection
        logger.info("collection_created", id=cid, name=name, creator=creator)
        return collection

    def get_collection(self, collection_id: str) -> Optional[NFTCollection]:
        return self._collections.get(collection_id)

    def list_collections(self, collection_type: str = None, verified: bool = None,
                         sort_by: str = "total_volume", limit: int = 50) -> list[NFTCollection]:
        collections = list(self._collections.values())
        if collection_type:
            collections = [c for c in collections if c.collection_type == collection_type]
        if verified is not None:
            collections = [c for c in collections if c.verified == verified]

        sort_map = {
            "total_volume": lambda c: c.total_volume,
            "floor_price": lambda c: c.floor_price,
            "total_supply": lambda c: c.total_supply,
            "created": lambda c: c.created,
            "name": lambda c: c.name,
        }
        collections.sort(key=sort_map.get(sort_by, lambda c: c.total_volume), reverse=True)
        return collections[:limit]

    # === NFT Minting ===

    def mint_nft(self, collection_id: str, to_address: str, name: str,
                 description: str = "", image: str = "", metadata_uri: str = "",
                 attributes: dict = None) -> Optional[NFTItem]:
        """Mint a new NFT in a collection."""
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        if collection.total_supply >= collection.max_supply:
            return None

        token_id = str(secrets.randbelow(999999) + 1)
        nft_id = f"nft-{secrets.token_hex(8)}"

        nft = NFTItem(
            id=nft_id, token_id=token_id, collection_id=collection_id,
            collection_name=collection.name, owner=to_address,
            creator=collection.creator, name=name,
            description=description, image=image,
            metadata_uri=metadata_uri, attributes=attributes or {},
            standard=collection.standard,
        )

        with self._lock:
            self._nfts[nft_id] = nft
            collection.total_supply += 1

            # Record transfer
            transfer = NFTTransfer(
                id=f"trx-{secrets.token_hex(8)}", nft_id=nft_id, token_id=token_id,
                collection_id=collection_id, from_address="", to_address=to_address,
                tx_type="mint",
            )
            self._transfers.append(transfer)

        logger.info("nft_minted", id=nft_id, collection=collection_id, to=to_address)
        return nft

    def get_nft(self, nft_id: str) -> Optional[NFTItem]:
        return self._nfts.get(nft_id)

    def list_nfts(self, collection_id: str = None, owner: str = None,
                  listed: bool = None, limit: int = 50,
                  sort_by: str = "minted_at") -> list[NFTItem]:
        nfts = list(self._nfts.values())
        if collection_id:
            nfts = [n for n in nfts if n.collection_id == collection_id]
        if owner:
            nfts = [n for n in nfts if n.owner == owner]
        if listed is not None:
            nfts = [n for n in nfts if n.listed == listed]

        sort_map = {
            "minted_at": lambda n: n.minted_at,
            "last_sale_price": lambda n: n.last_sale_price,
            "name": lambda n: n.name,
            "transfer_count": lambda n: n.transfer_count,
        }
        nfts.sort(key=sort_map.get(sort_by, lambda n: n.minted_at), reverse=True)
        return nfts[:limit]

    # === Listings ===

    def create_listing(self, nft_id: str, seller: str, price: float,
                       listing_type: str = ListingType.FIXED.value,
                       currency: str = "VRS", expires_days: int = 30) -> Optional[Listing]:
        """Create a listing for an NFT."""
        nft = self._nfts.get(nft_id)
        if not nft or nft.owner != seller:
            return None
        if nft.listed:
            return None  # Already listed
        if price <= 0:
            return None

        listing_id = f"lst-{secrets.token_hex(8)}"
        expires = (datetime.utcnow() + timedelta(days=expires_days)).isoformat() if expires_days > 0 else ""

        listing = Listing(
            id=listing_id, nft_id=nft_id, token_id=nft.token_id,
            collection_id=nft.collection_id, collection_name=nft.collection_name,
            seller=seller, listing_type=listing_type, price=price,
            currency=currency, expires_at=expires,
        )

        with self._lock:
            self._listings[listing_id] = listing
            nft.listed = True

            # Update floor price
            collection = self._collections.get(nft.collection_id)
            if collection:
                collection.floor_price = min(collection.floor_price or price, price) if price > 0 else collection.floor_price

        logger.info("listing_created", id=listing_id, nft=nft_id, price=price)
        return listing

    def cancel_listing(self, listing_id: str) -> Optional[Listing]:
        listing = self._listings.get(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE.value:
            return None
        listing.status = ListingStatus.CANCELLED.value

        nft = self._nfts.get(listing.nft_id)
        if nft:
            nft.listed = False

        return listing

    def buy_nft(self, listing_id: str, buyer: str) -> Optional[dict]:
        """Buy an NFT from a fixed-price listing."""
        listing = self._listings.get(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE.value:
            return None
        if listing.listing_type != ListingType.FIXED.value:
            return None

        nft = self._nfts.get(listing.nft_id)
        if not nft:
            return None

        # Process sale
        seller = listing.seller
        price = listing.price
        collection = self._collections.get(nft.collection_id)
        royalty = price * (collection.royalty_bps / 10000) if collection else 0

        listing.status = ListingStatus.SOLD.value
        listing.buyer = buyer
        listing.sold_at = datetime.utcnow().isoformat()
        listing.sold_price = price

        nft.owner = buyer
        nft.listed = False
        nft.last_sale_price = price
        nft.last_sale_date = datetime.utcnow().isoformat()
        nft.transfer_count += 1

        if collection:
            collection.total_volume += price

        # Record transfer
        transfer = NFTTransfer(
            id=f"trx-{secrets.token_hex(8)}", nft_id=nft.id, token_id=nft.token_id,
            collection_id=nft.collection_id, from_address=seller, to_address=buyer,
            price=price, currency=listing.currency, tx_type="sale",
        )
        self._transfers.append(transfer)

        return {
            "listing": listing.to_dict(),
            "nft": nft.to_dict(),
            "price": price,
            "royalty": round(royalty, 4),
            "buyer": buyer,
            "seller": seller,
        }

    def get_listing(self, listing_id: str) -> Optional[Listing]:
        return self._listings.get(listing_id)

    def list_listings(self, collection_id: str = None, listing_type: str = None,
                      status: str = None, seller: str = None,
                      min_price: float = None, max_price: float = None,
                      sort_by: str = "price", limit: int = 50) -> list[Listing]:
        listings = list(self._listings.values())
        if collection_id:
            listings = [l for l in listings if l.collection_id == collection_id]
        if listing_type:
            listings = [l for l in listings if l.listing_type == listing_type]
        if status:
            listings = [l for l in listings if l.status == status]
        if seller:
            listings = [l for l in listings if l.seller == seller]
        if min_price is not None:
            listings = [l for l in listings if l.price >= min_price]
        if max_price is not None:
            listings = [l for l in listings if l.price <= max_price]

        sort_map = {
            "price": lambda l: l.price,
            "created": lambda l: l.created,
            "views": lambda l: l.views,
            "favorites": lambda l: l.favorites,
        }
        listings.sort(key=sort_map.get(sort_by, lambda l: l.price))
        return listings[:limit]

    def increment_views(self, listing_id: str):
        listing = self._listings.get(listing_id)
        if listing:
            listing.views += 1

    # === Auctions ===

    def place_bid(self, listing_id: str, bidder: str, amount: float) -> Optional[Bid]:
        """Place a bid on an auction listing."""
        listing = self._listings.get(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE.value:
            return None
        if listing.listing_type != ListingType.AUCTION.value:
            return None

        # Check if bid is higher than current highest
        existing_bids = self._bids.get(listing_id, [])
        if existing_bids and amount <= max(b.amount for b in existing_bids):
            return None

        bid_id = f"bid-{secrets.token_hex(8)}"
        bid = Bid(
            id=bid_id, listing_id=listing_id, nft_id=listing.nft_id,
            bidder=bidder, amount=amount,
            expires_at=listing.expires_at,
        )
        self._bids[listing_id].append(bid)

        # Update listing price to current highest bid
        listing.price = amount

        logger.info("bid_placed", bid_id=bid_id, listing=listing_id, amount=amount)
        return bid

    def end_auction(self, listing_id: str) -> Optional[dict]:
        """End an auction and transfer the NFT to the winner."""
        listing = self._listings.get(listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE.value:
            return None
        if listing.listing_type != ListingType.AUCTION.value:
            return None

        bids = self._bids.get(listing_id, [])
        if not bids:
            listing.status = ListingStatus.CANCELLED.value
            nft = self._nfts.get(listing.nft_id)
            if nft:
                nft.listed = False
            return {"result": "cancelled", "reason": "no_bids"}

        # Find highest bid
        highest = max(bids, key=lambda b: b.amount)
        highest.status = "won"

        # Mark other bids as lost
        for b in bids:
            if b.id != highest.id:
                b.status = "lost"

        nft = self._nfts.get(listing.nft_id)
        if not nft:
            return None

        collection = self._collections.get(nft.collection_id)
        royalty = highest.amount * (collection.royalty_bps / 10000) if collection else 0

        listing.status = ListingStatus.SOLD.value
        listing.buyer = highest.bidder
        listing.sold_at = datetime.utcnow().isoformat()
        listing.sold_price = highest.amount

        nft.owner = highest.bidder
        nft.listed = False
        nft.last_sale_price = highest.amount
        nft.last_sale_date = datetime.utcnow().isoformat()
        nft.transfer_count += 1

        if collection:
            collection.total_volume += highest.amount

        transfer = NFTTransfer(
            id=f"trx-{secrets.token_hex(8)}", nft_id=nft.id, token_id=nft.token_id,
            collection_id=nft.collection_id, from_address=listing.seller,
            to_address=highest.bidder, price=highest.amount, tx_type="sale",
        )
        self._transfers.append(transfer)

        return {
            "result": "sold",
            "winner": highest.bidder,
            "price": highest.amount,
            "royalty": round(royalty, 4),
            "bid_count": len(bids),
        }

    def list_bids(self, listing_id: str) -> list[Bid]:
        return sorted(self._bids.get(listing_id, []), key=lambda b: b.amount, reverse=True)

    # === Transfers ===

    def transfer_nft(self, nft_id: str, from_address: str, to_address: str) -> Optional[NFTItem]:
        """Transfer an NFT (non-sale)."""
        nft = self._nfts.get(nft_id)
        if not nft or nft.owner != from_address:
            return None
        if nft.listed:
            return None

        nft.owner = to_address
        nft.transfer_count += 1

        transfer = NFTTransfer(
            id=f"trx-{secrets.token_hex(8)}", nft_id=nft_id, token_id=nft.token_id,
            collection_id=nft.collection_id, from_address=from_address,
            to_address=to_address, tx_type="transfer",
        )
        self._transfers.append(transfer)
        return nft

    def list_transfers(self, nft_id: str = None, collection_id: str = None,
                       limit: int = 50) -> list[NFTTransfer]:
        transfers = list(self._transfers)
        if nft_id:
            transfers = [t for t in transfers if t.nft_id == nft_id]
        if collection_id:
            transfers = [t for t in transfers if t.collection_id == collection_id]
        transfers.reverse()
        return transfers[:limit]

    # === Favorites ===

    def toggle_favorite(self, user: str, nft_id: str) -> bool:
        if nft_id in self._favorites[user]:
            self._favorites[user].discard(nft_id)
            return False
        else:
            self._favorites[user].add(nft_id)
            # Update listing favorite count
            for l in self._listings.values():
                if l.nft_id == nft_id:
                    l.favorites += 1
                    break
            return True

    def get_favorites(self, user: str) -> list[str]:
        return list(self._favorites.get(user, set()))

    # === Stats ===

    def get_stats(self) -> dict:
        total_nfts = len(self._nfts)
        total_collections = len(self._collections)
        active_listings = sum(1 for l in self._listings.values() if l.status == "active")
        sold = sum(1 for l in self._listings.values() if l.status == "sold")
        total_volume = sum(l.sold_price for l in self._listings.values() if l.status == "sold")
        total_transfers = len(self._transfers)
        active_auctions = sum(1 for l in self._listings.values() if l.listing_type == "auction" and l.status == "active")
        total_bids = sum(len(bids) for bids in self._bids.values())

        return {
            "total_nfts": total_nfts,
            "total_collections": total_collections,
            "active_listings": active_listings,
            "active_auctions": active_auctions,
            "sold_listings": sold,
            "total_volume": round(total_volume, 2),
            "total_transfers": total_transfers,
            "total_bids": total_bids,
            "avg_sale_price": round(total_volume / max(1, sold), 2),
        }

    def get_collection_stats(self, collection_id: str) -> Optional[dict]:
        collection = self._collections.get(collection_id)
        if not collection:
            return None
        nfts = [n for n in self._nfts.values() if n.collection_id == collection_id]
        listings = [l for l in self._listings.values() if l.collection_id == collection_id and l.status == "active"]
        owners = len(set(n.owner for n in nfts))
        return {
            "collection": collection.to_dict(),
            "nft_count": len(nfts),
            "active_listings": len(listings),
            "owners": owners,
            "floor_price": collection.floor_price,
            "total_volume": round(collection.total_volume, 2),
        }

    def get_dashboard(self) -> dict:
        return {
            "stats": self.get_stats(),
            "top_collections": [c.to_dict() for c in self.list_collections(sort_by="total_volume", limit=10)],
            "recent_listings": [l.to_dict() for l in self.list_listings(status="active", sort_by="created", limit=10)],
            "recent_sales": [l.to_dict() for l in self.list_listings(status="sold", sort_by="sold_at", limit=10)],
            "monitoring": self._monitoring,
        }

    # === Monitoring ===

    def start_monitoring(self, interval: int = 60):
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()
        logger.info("nft_monitoring_started", interval=interval)

    def stop_monitoring(self):
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int):
        while self._monitoring:
            try:
                # Check for expired listings
                now = datetime.utcnow()
                for listing in self._listings.values():
                    if listing.status == "active" and listing.expires_at:
                        try:
                            exp = datetime.fromisoformat(listing.expires_at.replace("Z", ""))
                            if now > exp:
                                listing.status = "expired"
                                nft = self._nfts.get(listing.nft_id)
                                if nft:
                                    nft.listed = False
                        except Exception:
                            pass
                # End expired auctions
                for listing in self._listings.values():
                    if listing.status == "active" and listing.listing_type == "auction":
                        if listing.expires_at:
                            try:
                                exp = datetime.fromisoformat(listing.expires_at.replace("Z", ""))
                                if now > exp:
                                    self.end_auction(listing.id)
                            except Exception:
                                pass
            except Exception as e:
                logger.error("monitor_error", error=str(e))
            time.sleep(interval)

    def is_monitoring(self) -> bool:
        return self._monitoring


_service: Optional[NFTMarketplaceService] = None

def get_nft_marketplace_service() -> NFTMarketplaceService:
    global _service
    if _service is None:
        _service = NFTMarketplaceService()
    return _service
