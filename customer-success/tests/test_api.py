"""Tests for Customer Success Platform."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "customer-success"

def test_list_agents(client):
    response = client.get("/api/v1/chat/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == 5

def test_ticket_types(client):
    response = client.get("/api/v1/tickets/types/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data["types"]) == 12

def test_ticket_priorities(client):
    response = client.get("/api/v1/tickets/priorities/list")
    assert response.status_code == 200
    assert "critical" in response.json()["priorities"]

def test_ticket_statuses(client):
    response = client.get("/api/v1/tickets/statuses/list")
    assert response.status_code == 200
    assert "open" in response.json()["statuses"]

def test_create_ticket(client):
    response = client.post("/api/v1/tickets/", json={
        "title": "Test Ticket",
        "type": "technical",
        "priority": "medium",
        "description": "Test description",
        "user_id": "test@example.com",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Ticket"
    assert data["status"] == "open"
    assert data["department"] == "Engineering"

def test_list_tickets(client):
    response = client.get("/api/v1/tickets/")
    assert response.status_code == 200
    assert "tickets" in response.json()

def test_ticket_stats(client):
    response = client.get("/api/v1/tickets/stats/dashboard")
    assert response.status_code == 200

def test_knowledge_search(client):
    response = client.post("/api/v1/knowledge/search", json={
        "query": "blockchain",
        "limit": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0

def test_knowledge_categories(client):
    response = client.get("/api/v1/knowledge/categories/list")
    assert response.status_code == 200
    assert "documentation" in response.json()["categories"]

def test_incident_types(client):
    response = client.get("/api/v1/incidents/types/list")
    assert response.status_code == 200
    assert "rpc_unavailable" in response.json()["types"]

def test_escalation_reasons(client):
    response = client.get("/api/v1/escalation/reasons/list")
    assert response.status_code == 200
    assert "legal" in response.json()["reasons"]

def test_analytics_dashboard(client):
    response = client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    assert "metrics" in response.json()

def test_learning_solutions(client):
    response = client.get("/api/v1/learning/solutions")
    assert response.status_code == 200

def test_developer_api_reference(client):
    response = client.get("/api/v1/developer/api-reference")
    assert response.status_code == 200
    assert "base_url" in response.json()
