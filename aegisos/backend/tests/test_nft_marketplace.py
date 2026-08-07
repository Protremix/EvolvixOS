"""Tests for NFT Marketplace — Phase 45."""

import pytest
import time
from app.services.nft_marketplace import (
    NFTMarketplaceService, get_nft_marketplace_service, ListingType, ListingStatus, CollectionType,
)


class TestCollections:
    def test_list_collections(self):
        service = NFTMarketplaceService()
        cols = service.list_collections()
        assert len(cols) >= 5

    def test_create_collection(self):
        service = NFTMarketplaceService()
        c = service.create_collection("Test Col", "Desc", "0xcreator")
        assert c.id.startswith("col-")

    def test_get_collection(self):
        service = NFTMarketplaceService()
        cols = service.list_collections()
        found = service.get_collection(cols[0].id)
        assert found is not None

    def test_filter_by_type(self):
        service = NFTMarketplaceService()
        art = service.list_collections(collection_type="art")
        assert all(c.collection_type == "art" for c in art)

    def test_collection_stats(self):
        service = NFTMarketplaceService()
        cols = service.list_collections()
        stats = service.get_collection_stats(cols[0].id)
        assert stats is not None
        assert "nft_count" in stats


class TestMinting:
    def test_mint_nft(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xuser", "Test NFT")
        assert nft.id.startswith("nft-")
        assert nft.name == "Test NFT"

    def test_mint_invalid_collection(self):
        service = NFTMarketplaceService()
        nft = service.mint_nft("invalid", "0xuser", "Test")
        assert nft is None

    def test_get_nft(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xuser", "Test")
        found = service.get_nft(nft.id)
        assert found is not None

    def test_list_nfts(self):
        service = NFTMarketplaceService()
        nfts = service.list_nfts()
        assert len(nfts) > 0

    def test_list_nfts_by_collection(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nfts = service.list_nfts(collection_id=col.id)
        assert all(n.collection_id == col.id for n in nfts)

    def test_list_nfts_by_owner(self):
        service = NFTMarketplaceService()
        nft = service.mint_nft(service.list_collections()[0].id, "0xowner_test", "Test")
        nfts = service.list_nfts(owner="0xowner_test")
        assert all(n.owner == "0xowner_test" for n in nfts)


class TestListings:
    def test_create_listing(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 100)
        assert listing.id.startswith("lst-")
        assert listing.price == 100

    def test_create_listing_not_owner(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xwrong", 100)
        assert listing is None

    def test_cancel_listing(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 100)
        cancelled = service.cancel_listing(listing.id)
        assert cancelled.status == "cancelled"

    def test_list_listings(self):
        service = NFTMarketplaceService()
        listings = service.list_listings()
        assert len(listings) > 0

    def test_filter_listings_by_status(self):
        service = NFTMarketplaceService()
        active = service.list_listings(status="active")
        assert all(l.status == "active" for l in active)

    def test_filter_listings_by_type(self):
        service = NFTMarketplaceService()
        auctions = service.list_listings(listing_type="auction")
        assert all(l.listing_type == "auction" for l in auctions)

    def test_filter_by_price_range(self):
        service = NFTMarketplaceService()
        filtered = service.list_listings(min_price=10, max_price=100)
        assert all(10 <= l.price <= 100 for l in filtered)


class TestBuying:
    def test_buy_nft(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 100)
        result = service.buy_nft(listing.id, "0xbuyer")
        assert result is not None
        assert result["buyer"] == "0xbuyer"
        assert result["price"] == 100

    def test_buy_nonexistent_listing(self):
        service = NFTMarketplaceService()
        result = service.buy_nft("invalid", "0xbuyer")
        assert result is None

    def test_buy_already_sold(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 100)
        service.buy_nft(listing.id, "0xbuyer1")
        result = service.buy_nft(listing.id, "0xbuyer2")
        assert result is None


class TestAuctions:
    def test_place_bid(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 50, listing_type="auction")
        bid = service.place_bid(listing.id, "0xbidder1", 60)
        assert bid is not None
        assert bid.amount == 60

    def test_bid_too_low(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 50, listing_type="auction")
        service.place_bid(listing.id, "0xbidder1", 100)
        bid = service.place_bid(listing.id, "0xbidder2", 50)
        assert bid is None

    def test_end_auction(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 50, listing_type="auction")
        service.place_bid(listing.id, "0xbidder1", 100)
        service.place_bid(listing.id, "0xbidder2", 150)
        result = service.end_auction(listing.id)
        assert result["result"] == "sold"
        assert result["winner"] == "0xbidder2"

    def test_end_auction_no_bids(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 50, listing_type="auction")
        result = service.end_auction(listing.id)
        assert result["result"] == "cancelled"

    def test_list_bids(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xseller", "Test")
        listing = service.create_listing(nft.id, "0xseller", 50, listing_type="auction")
        service.place_bid(listing.id, "0xb1", 60)
        service.place_bid(listing.id, "0xb2", 100)
        bids = service.list_bids(listing.id)
        assert len(bids) == 2
        assert bids[0].amount >= bids[1].amount


class TestTransfers:
    def test_transfer_nft(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xowner", "Test")
        result = service.transfer_nft(nft.id, "0xowner", "0xnew")
        assert result.owner == "0xnew"

    def test_transfer_not_owner(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        nft = service.mint_nft(col.id, "0xowner", "Test")
        result = service.transfer_nft(nft.id, "0xwrong", "0xnew")
        assert result is None

    def test_list_transfers(self):
        service = NFTMarketplaceService()
        col = service.list_collections()[0]
        service.mint_nft(col.id, "0xuser", "Transfer Test")  # Creates a mint transfer
        transfers = service.list_transfers()
        assert len(transfers) > 0


class TestFavorites:
    def test_toggle_favorite(self):
        service = NFTMarketplaceService()
        nfts = service.list_nfts()
        result = service.toggle_favorite("0xuser", nfts[0].id)
        assert result is True

    def test_untoggle_favorite(self):
        service = NFTMarketplaceService()
        nfts = service.list_nfts()
        service.toggle_favorite("0xuser", nfts[0].id)
        result = service.toggle_favorite("0xuser", nfts[0].id)
        assert result is False

    def test_get_favorites(self):
        service = NFTMarketplaceService()
        nfts = service.list_nfts()
        service.toggle_favorite("0xuser", nfts[0].id)
        favs = service.get_favorites("0xuser")
        assert nfts[0].id in favs


class TestStats:
    def test_stats(self):
        service = NFTMarketplaceService()
        stats = service.get_stats()
        assert stats["total_nfts"] > 0
        assert stats["total_collections"] > 0

    def test_dashboard(self):
        service = NFTMarketplaceService()
        dash = service.get_dashboard()
        assert "stats" in dash
        assert "top_collections" in dash
        assert "recent_listings" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = NFTMarketplaceService()
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(2)
        service.stop_monitoring()
        assert service.is_monitoring() is False


class TestNFTAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/nft/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_collections(self, client, test_user):
        resp = client.get("/api/v1/nft/collections", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) >= 5

    def test_create_collection(self, client, test_user):
        resp = client.post("/api/v1/nft/collections", json={
            "name": "Test", "description": "Test", "creator": "0x1",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_mint(self, client, test_user):
        cols = client.get("/api/v1/nft/collections", headers=test_user["headers"]).json()
        resp = client.post("/api/v1/nft/mint", json={
            "collection_id": cols[0]["id"], "to_address": "0xuser", "name": "Test NFT",
        }, headers=test_user["headers"])
        assert resp.status_code == 200

    def test_listings(self, client, test_user):
        resp = client.get("/api/v1/nft/listings", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_nfts(self, client, test_user):
        resp = client.get("/api/v1/nft/nfts", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/nft/stats", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_nft_marketplace_service() is get_nft_marketplace_service()
