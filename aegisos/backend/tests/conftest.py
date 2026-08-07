import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"

from app.models.base import Base
from app.models import User, UserRole, Project, Task, Event  # noqa
from app.db.session import get_db
from app.core.security import create_access_token, create_refresh_token, password_hash
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db):
    user = User(
        username="testuser",
        email="user@evolvixos.com",
        hashed_password=password_hash("password123"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    return {
        "user": user,
        "email": user.email,
        "username": user.username,
        "password": "password123",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="function")
def test_admin(test_db):
    admin = User(
        username="testadmin",
        email="admin@evolvixos.com",
        hashed_password=password_hash("adminpassword123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)

    access_token = create_access_token(str(admin.id), admin.role.value)
    refresh_token = create_refresh_token(str(admin.id))

    return {
        "user": admin,
        "email": admin.email,
        "username": admin.username,
        "password": "adminpassword123",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="function")
def test_viewer(test_db):
    viewer = User(
        username="testviewer",
        email="viewer@evolvixos.com",
        hashed_password=password_hash("viewerpassword123"),
        role=UserRole.VIEWER,
        is_active=True,
    )
    test_db.add(viewer)
    test_db.commit()
    test_db.refresh(viewer)

    access_token = create_access_token(str(viewer.id), viewer.role.value)
    refresh_token = create_refresh_token(str(viewer.id))

    return {
        "user": viewer,
        "email": viewer.email,
        "username": viewer.username,
        "password": "viewerpassword123",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest.fixture(scope="function")
def test_project(test_db, test_user):
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=test_user["user"].id,
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project
