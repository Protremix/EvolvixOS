from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@evolvixos.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@evolvixos.com"
    assert data["username"] == "newuser"


def test_register_duplicate_email(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "another",
            "email": "user@evolvixos.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 400


def test_login_valid(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient, test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"email": test_user["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_user):
    response = client.get(
        "/api/v1/auth/me",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]


def test_get_current_user_no_token(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
