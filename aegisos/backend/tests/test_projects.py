from fastapi.testclient import TestClient


def test_create_project(client: TestClient, test_user):
    response = client.post(
        "/api/v1/projects/",
        json={"name": "New Project", "description": "Test description"},
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"


def test_list_projects(client: TestClient, test_user, test_project):
    response = client.get("/api/v1/projects/", headers=test_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_project(client: TestClient, test_user, test_project):
    response = client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"


def test_update_project(client: TestClient, test_user, test_project):
    response = client.put(
        f"/api/v1/projects/{test_project.id}",
        json={"name": "Updated Project"},
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"


def test_delete_project(client: TestClient, test_user, test_project):
    response = client.delete(
        f"/api/v1/projects/{test_project.id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 204


def test_create_project_unauthorized(client: TestClient):
    response = client.post(
        "/api/v1/projects/",
        json={"name": "Test"},
    )
    assert response.status_code == 401


def test_create_project_viewer_role(client: TestClient, test_viewer):
    response = client.post(
        "/api/v1/projects/",
        json={"name": "Test"},
        headers=test_viewer["headers"],
    )
    assert response.status_code == 403
