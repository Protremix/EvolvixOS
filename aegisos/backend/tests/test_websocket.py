"""
Tests for the WebSocket real-time update system.
"""

import pytest
import json
from app.core.websocket_manager import ws_manager


class TestWebSocketManager:
    """Test the WebSocket connection manager."""

    def test_manager_initialization(self):
        assert ws_manager.connection_count == 0
        assert ws_manager.active_connections == set()

    def test_broadcast_no_connections(self):
        """Broadcast should not fail with no connections."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(ws_manager.broadcast("test", {"msg": "hello"}))
        finally:
            loop.close()
        # Should complete without error

    def test_send_personal_no_connection(self):
        """send_personal should handle missing connections gracefully."""
        import asyncio

        class FakeWS:
            async def send_text(self, text):
                raise ConnectionError("Not connected")

        fake = FakeWS()
        ws_manager.active_connections.add(fake)
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(ws_manager.send_personal(fake, "test", {"msg": "hi"}))
        finally:
            loop.close()
        # Should have removed the dead connection
        assert fake not in ws_manager.active_connections

    def test_connection_count(self):
        assert ws_manager.connection_count == len(ws_manager.active_connections)


class TestWebSocketAPI:
    """Test WebSocket API endpoints."""

    def test_ws_status_endpoint(self, client):
        """Test the REST status endpoint."""
        response = client.get("/api/v1/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "status" in data
        assert data["active_connections"] >= 0

    def test_ws_endpoint_requires_token(self, client):
        """WebSocket should reject connections without a token."""
        # TestClient WebSocket support
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws"):
                pass

    def test_ws_endpoint_invalid_token(self, client, test_user):
        """WebSocket should reject invalid tokens."""
        with pytest.raises(Exception):
            with client.websocket_connect("/api/v1/ws?token=invalid_token"):
                pass

    def test_ws_endpoint_valid_token(self, client, test_user):
        """WebSocket should accept valid tokens and send initial state."""
        token = test_user["access_token"]
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            # Should receive initial_state message
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "initial_state"
            assert "agents" in msg["data"]
            assert "agent_count" in msg["data"]

    def test_ws_ping_pong(self, client, test_user):
        """Test ping/pong heartbeat."""
        token = test_user["access_token"]
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            # Receive initial state first
            ws.receive_text()
            # Send ping
            ws.send_text(json.dumps({"action": "ping"}))
            # Receive pong
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "pong"

    def test_ws_status_query(self, client, test_user):
        """Test status query via WebSocket."""
        token = test_user["access_token"]
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            ws.receive_text()  # initial_state
            ws.send_text(json.dumps({"action": "status"}))
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "status"
            assert "connections" in msg["data"]

    def test_ws_invalid_json(self, client, test_user):
        """Test handling of invalid JSON messages."""
        token = test_user["access_token"]
        with client.websocket_connect(f"/api/v1/ws?token={token}") as ws:
            ws.receive_text()  # initial_state
            ws.send_text("not json")
            data = ws.receive_text()
            msg = json.loads(data)
            assert msg["type"] == "error"
