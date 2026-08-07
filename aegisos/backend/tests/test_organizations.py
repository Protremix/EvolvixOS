"""Tests for organization endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_create_organization(client, test_user):
    """Test creating an organization."""
    response = client.post(
        "/api/v1/organizations/",
        json={"name": "Test Org", "description": "A test organization"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Org"
    assert data["slug"] == "test-org"
    assert data["owner_id"] == str(test_user["user"].id)
    assert data["is_active"] is True


def test_list_organizations(client, test_user):
    """Test listing organizations."""
    # Create an org first
    client.post(
        "/api/v1/organizations/",
        json={"name": "List Test Org"},
        headers=test_user["headers"],
    )
    
    response = client.get(
        "/api/v1/organizations/",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "List Test Org"


def test_get_organization(client, test_user):
    """Test getting organization details."""
    create_resp = client.post(
        "/api/v1/organizations/",
        json={"name": "Get Test Org"},
        headers=test_user["headers"],
    )
    org_id = create_resp.json()["id"]
    
    response = client.get(
        f"/api/v1/organizations/{org_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test Org"


def test_update_organization(client, test_user):
    """Test updating an organization."""
    create_resp = client.post(
        "/api/v1/organizations/",
        json={"name": "Update Test Org"},
        headers=test_user["headers"],
    )
    org_id = create_resp.json()["id"]
    
    response = client.put(
        f"/api/v1/organizations/{org_id}",
        json={"name": "Updated Org Name", "description": "Updated description"},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Org Name"
    assert data["slug"] == "updated-org-name"
    assert data["description"] == "Updated description"


def test_delete_organization(client, test_user):
    """Test archiving an organization."""
    create_resp = client.post(
        "/api/v1/organizations/",
        json={"name": "Delete Test Org"},
        headers=test_user["headers"],
    )
    org_id = create_resp.json()["id"]
    
    response = client.delete(
        f"/api/v1/organizations/{org_id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 204


def test_list_members(client, test_user):
    """Test listing organization members."""
    create_resp = client.post(
        "/api/v1/organizations/",
        json={"name": "Members Test Org"},
        headers=test_user["headers"],
    )
    org_id = create_resp.json()["id"]
    
    response = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["role"] == "admin"  # Owner should be admin


def test_create_organization_unauthorized(client):
    """Test creating an organization without auth."""
    response = client.post(
        "/api/v1/organizations/",
        json={"name": "Unauthorized Org"},
    )
    assert response.status_code == 401
