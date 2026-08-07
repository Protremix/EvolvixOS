"""Tests for Block Explorer — Phase 47."""

import pytest
import time
from app.services.block_explorer import (
    BlockExplorerService, get_block_explorer_service, TxStatus, TxType,
)


class TestBlocks:
    def test_list_blocks(self):
        service = BlockExplorerService()
        blocks = service.list_blocks(limit=10)
        assert len(blocks) == 10

    def test_get_block_by_height(self):
        service = BlockExplorerService()
        blocks = service.list_blocks(limit=1)
        block = service.get_block(height=blocks[0].height)
        assert block is not None

    def test_get_block_by_hash(self):
        service = BlockExplorerService()
        blocks = service.list_blocks(limit=1)
        block = service.get_block(block_hash=blocks[0].hash)
        assert block is not None
        assert block.height == blocks[0].height

    def test_get_latest_blocks(self):
        service = BlockExplorerService()
        latest = service.get_latest_blocks(5)
        assert len(latest) == 5
        heights = [b.height for b in latest]
        assert heights == sorted(heights, reverse=True)

    def test_block_transactions(self):
        service = BlockExplorerService()
        blocks = service.list_blocks(limit=1)
        txs = service.get_block_transactions(blocks[0].height)
        assert len(txs) > 0

    def test_block_not_found(self):
        service = BlockExplorerService()
        assert service.get_block(height=999999999) is None


class TestTransactions:
    def test_list_transactions(self):
        service = BlockExplorerService()
        txs = service.list_transactions(limit=10)
        assert len(txs) > 0

    def test_get_transaction(self):
        service = BlockExplorerService()
        txs = service.list_transactions(limit=1)
        tx = service.get_transaction(txs[0].hash)
        assert tx is not None

    def test_filter_by_type(self):
        service = BlockExplorerService()
        transfers = service.list_transactions(tx_type="transfer")
        assert all(t.tx_type == "transfer" for t in transfers)

    def test_filter_by_status(self):
        service = BlockExplorerService()
        success = service.list_transactions(status="success")
        assert all(t.status == "success" for t in success)

    def test_filter_by_address(self):
        service = BlockExplorerService()
        txs = service.list_transactions(limit=5)
        if txs:
            addr = txs[0].from_address
            if addr:
                filtered = service.list_transactions(address=addr)
                assert all(t.from_address == addr or t.to_address == addr for t in filtered)

    def test_sort_by_value(self):
        service = BlockExplorerService()
        txs = service.list_transactions(sort_by="value", limit=10)
        values = [t.value for t in txs]
        assert values == sorted(values, reverse=True)


class TestAddresses:
    def test_get_address(self):
        service = BlockExplorerService()
        addrs = service.list_top_addresses(limit=1)
        addr = service.get_address(addrs[0].address)
        assert addr is not None

    def test_address_transactions(self):
        service = BlockExplorerService()
        addrs = service.list_top_addresses(limit=1)
        txs = service.get_address_transactions(addrs[0].address)
        assert len(txs) >= 0

    def test_top_addresses(self):
        service = BlockExplorerService()
        addrs = service.list_top_addresses(sort_by="balance", limit=10)
        assert len(addrs) > 0

    def test_top_addresses_by_tx_count(self):
        service = BlockExplorerService()
        addrs = service.list_top_addresses(sort_by="tx_count", limit=10)
        assert len(addrs) > 0


class TestContracts:
    def test_list_contracts(self):
        service = BlockExplorerService()
        contracts = service.list_contracts()
        assert len(contracts) > 0

    def test_get_contract(self):
        service = BlockExplorerService()
        contracts = service.list_contracts(limit=1)
        contract = service.get_contract(contracts[0].address)
        assert contract is not None

    def test_filter_verified(self):
        service = BlockExplorerService()
        verified = service.list_contracts(verified=True)
        assert all(c.verified for c in verified)

    def test_filter_by_standard(self):
        service = BlockExplorerService()
        vrc20 = service.list_contracts(standard="VRC-20")
        assert all(c.standard == "VRC-20" for c in vrc20)


class TestEventLogs:
    def test_list_logs(self):
        service = BlockExplorerService()
        logs = service.list_logs(limit=10)
        assert len(logs) > 0

    def test_filter_by_address(self):
        service = BlockExplorerService()
        logs = service.list_logs(limit=5)
        if logs:
            filtered = service.list_logs(address=logs[0].address)
            assert all(l.address == logs[0].address for l in filtered)

    def test_filter_by_block(self):
        service = BlockExplorerService()
        logs = service.list_logs(limit=5)
        if logs:
            filtered = service.list_logs(block_height=logs[0].block_height)
            assert all(l.block_height == logs[0].block_height for l in filtered)


class TestSearch:
    def test_search_block_height(self):
        service = BlockExplorerService()
        blocks = service.list_blocks(limit=1)
        result = service.search(str(blocks[0].height))
        assert result["type"] == "block"

    def test_search_tx_hash(self):
        service = BlockExplorerService()
        txs = service.list_transactions(limit=1)
        result = service.search(txs[0].hash)
        assert result["type"] == "transaction"

    def test_search_address(self):
        service = BlockExplorerService()
        addrs = service.list_top_addresses(limit=1)
        result = service.search(addrs[0].address)
        assert result["type"] == "address"

    def test_search_not_found(self):
        service = BlockExplorerService()
        result = service.search("0xnonexistent1234567890123456789012345678")
        assert "error" in result or result["type"] == "unknown"


class TestNetworkStats:
    def test_stats(self):
        service = BlockExplorerService()
        stats = service.get_network_stats()
        assert stats["total_blocks"] > 0
        assert stats["total_transactions"] > 0
        assert "success_rate" in stats
        assert "tps" in stats

    def test_dashboard(self):
        service = BlockExplorerService()
        dash = service.get_dashboard()
        assert "network_stats" in dash
        assert "latest_blocks" in dash
        assert "latest_transactions" in dash
        assert "top_addresses" in dash
        assert "contracts" in dash


class TestMonitoring:
    def test_start_stop(self):
        service = BlockExplorerService()
        initial_height = service._current_height
        service.start_monitoring(interval=1)
        assert service.is_monitoring() is True
        time.sleep(3)
        service.stop_monitoring()
        assert service.is_monitoring() is False
        assert service._current_height > initial_height


class TestExplorerAPI:
    def test_dashboard(self, client, test_user):
        resp = client.get("/api/v1/explorer/dashboard", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_stats(self, client, test_user):
        resp = client.get("/api/v1/explorer/stats", headers=test_user["headers"])
        assert resp.status_code == 200
        assert resp.json()["total_blocks"] > 0

    def test_list_blocks(self, client, test_user):
        resp = client.get("/api/v1/explorer/blocks", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_get_block(self, client, test_user):
        blocks = client.get("/api/v1/explorer/blocks", headers=test_user["headers"]).json()
        resp = client.get(f"/api/v1/explorer/blocks/{blocks[0]['height']}", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_list_transactions(self, client, test_user):
        resp = client.get("/api/v1/explorer/transactions", headers=test_user["headers"])
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_search(self, client, test_user):
        resp = client.get("/api/v1/explorer/search?query=18000000", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_contracts(self, client, test_user):
        resp = client.get("/api/v1/explorer/contracts", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_logs(self, client, test_user):
        resp = client.get("/api/v1/explorer/logs", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_top_addresses(self, client, test_user):
        resp = client.get("/api/v1/explorer/addresses", headers=test_user["headers"])
        assert resp.status_code == 200

    def test_singleton(self):
        assert get_block_explorer_service() is get_block_explorer_service()
