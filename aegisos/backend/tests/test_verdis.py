"""
Tests for the Verdis blockchain integration.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.integrations.verdis import VerdisIntegration


class TestVerdisIntegration:
    """Test the Verdis integration adapter."""

    def test_rpc_call_mock(self):
        """Test that _rpc_call sends proper JSON-RPC."""
        integration = VerdisIntegration()

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"jsonrpc":"2.0","result":"ok","id":1}'
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_response):
            result = integration._rpc_call("system.health")
            assert result == "ok"

    def test_get_chain_health_disconnected(self):
        """Test health when RPC fails."""
        integration = VerdisIntegration()

        with patch.object(integration, '_rpc_call', return_value=None):
            health = integration.get_chain_health()
            assert health["connected"] is False
            assert health["chain_name"] == "Verdis"
            assert health["token_symbol"] == "VRDX"

    def test_get_chain_health_connected(self):
        """Test health when RPC returns data."""
        integration = VerdisIntegration()

        def mock_rpc(method, params=None):
            if method == "system.health":
                return {"isSyncing": False, "peers": 14, "shouldHavePeers": True}
            if method == "system.properties":
                return {"tokenSymbol": "VRDX", "tokenDecimals": 18, "ss58Format": 909}
            if method == "chain.getHeader":
                return {"number": "0x5f5", "hash": "0xabc", "parentHash": "0x123",
                        "stateRoot": "0xdef", "extrinsicsRoot": "0xghi"}
            if method == "state.getRuntimeVersion":
                return {"specVersion": 11, "implVersion": 6, "transactionVersion": 2,
                        "specName": "verdis", "implName": "verdis"}
            return None

        with patch.object(integration, '_rpc_call', side_effect=mock_rpc):
            health = integration.get_chain_health()
            assert health["connected"] is True
            assert health["peers"] == 14
            assert health["token_symbol"] == "VRDX"
            assert health["block_height"] == "0x5f5"
            assert health["spec_version"] == 11
            assert health["is_syncing"] is False

    def test_get_validators_dpos(self):
        """Test getting validators from DPoS pallet."""
        integration = VerdisIntegration()

        with patch.object(integration, '_rpc_call',
                          return_value=["5GrwvaEF...", "5FHneW46..."]):
            validators = integration.get_validators()
            assert len(validators) == 2
            assert validators[0]["address"] == "5GrwvaEF..."
            assert validators[0]["active"] is True

    def test_get_validators_session_fallback(self):
        """Test fallback to session validators."""
        integration = VerdisIntegration()

        def mock_rpc(method, params=None):
            if method == "dpos_activeValidators":
                return None
            if method == "session.validators":
                return ["5Alice...", "5Bob..."]
            return None

        with patch.object(integration, '_rpc_call', side_effect=mock_rpc):
            validators = integration.get_validators()
            assert len(validators) == 2

    def test_get_validators_empty(self):
        """Test when no validators available."""
        integration = VerdisIntegration()
        with patch.object(integration, '_rpc_call', return_value=None):
            validators = integration.get_validators()
            assert validators == []

    def test_get_network_info(self):
        """Test network info."""
        integration = VerdisIntegration()

        def mock_rpc(method, params=None):
            if method == "system.chain":
                return "Verdis"
            if method == "system.name":
                return "verdis-node"
            if method == "system.version":
                return "0.1.0"
            if method == "rpc.methods":
                return {"methods": ["system_health", "chain_getHeader", "state_getRuntimeVersion"]}
            return None

        with patch.object(integration, '_rpc_call', side_effect=mock_rpc):
            info = integration.get_network_info()
            assert info["chain"] == "Verdis"
            assert info["node_name"] == "verdis-node"
            assert info["node_version"] == "0.1.0"
            assert info["rpc_method_count"] == 3

    def test_health_summary(self):
        """Test human-readable health summary."""
        integration = VerdisIntegration()

        def mock_health():
            return {"connected": True, "chain_name": "Verdis", "token_symbol": "VRDX",
                    "ss58_prefix": 909, "block_height": "0x5f5", "peers": 14,
                    "is_syncing": False, "spec_version": 11}

        with patch.object(integration, 'get_chain_health', mock_health), \
             patch.object(integration, 'get_validators', return_value=[{"address": "5Alice", "active": True}]), \
             patch.object(integration, 'get_network_info', return_value={"node_name": "verdis-node", "node_version": "0.1.0", "rpc_method_count": 121, "consensus": "BABE/GRANDPA + DPoS"}):
            summary = integration.get_health_summary()
            assert "Verdis" in summary
            assert "Connected: True" in summary
            assert "VRDX" in summary
            assert "Validators: 1" in summary


class TestVerdisAPI:
    """Test Verdis API endpoints."""

    def test_health_unauthorized(self, client):
        response = client.get("/api/v1/verdis/health")
        assert response.status_code == 401

    def test_health_authorized(self, client, test_user):
        headers = test_user["headers"]

        from app.integrations.verdis import verdis
        with patch.object(verdis, 'get_chain_health',
                          return_value={"connected": True, "chain_name": "Verdis", "token_symbol": "VRDX",
                                        "block_height": "0x5f5", "peers": 14, "is_syncing": False, "spec_version": 11}), \
             patch.object(verdis, 'get_validators', return_value=[{"address": "5A", "active": True}]):
            response = client.get("/api/v1/verdis/health", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["connected"] is True
            assert data["token_symbol"] == "VRDX"
            assert data["peers"] == 14
            assert data["active_validators"] == 1

    def test_validators_authorized(self, client, test_user):
        headers = test_user["headers"]

        from app.integrations.verdis import verdis
        with patch.object(verdis, 'get_validators',
                          return_value=[{"address": "5Alice", "active": True}, {"address": "5Bob", "active": True}]):
            response = client.get("/api/v1/verdis/validators", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2

    def test_summary_authorized(self, client, test_user):
        headers = test_user["headers"]

        from app.integrations.verdis import verdis
        with patch.object(verdis, 'get_health_summary',
                          return_value="=== Verdis Health ===\nConnected: True"):
            response = client.get("/api/v1/verdis/summary", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "Verdis" in data["summary"]
