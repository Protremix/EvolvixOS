from fastapi.testclient import TestClient


def test_create_task(client: TestClient, test_user, test_project):
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Test Task",
            "description": "A test task",
            "project_id": str(test_project.id),
        },
        headers=test_user["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"


def test_list_tasks(client: TestClient, test_user, test_project):
    # First create a task
    client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task 1",
            "project_id": str(test_project.id),
        },
        headers=test_user["headers"],
    )
    # List tasks
    response = client.get("/api/v1/tasks/", headers=test_user["headers"])
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_list_tasks_by_project(client: TestClient, test_user, test_project):
    # Create a task
    client.post(
        "/api/v1/tasks/",
        json={
            "title": "Task for project",
            "project_id": str(test_project.id),
        },
        headers=test_user["headers"],
    )
    # List tasks filtered by project
    response = client.get(
        f"/api/v1/tasks/?project_id={test_project.id}",
        headers=test_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
