import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, SubscriptionTier
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        subscription_tier=SubscriptionTier.PRO
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.query(User).delete()
    db.commit()
    db.close()


def test_register_user():
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    assert "email" in response.json()


def test_login(test_user):
    response = client.post(
        "/api/v1/auth/login",
        params={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_create_benchmark(test_user):
    # Login first
    login_response = client.post(
        "/api/v1/auth/login",
        params={"email": "test@example.com", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]
    
    # Create benchmark
    response = client.post(
        "/api/v1/benchmark",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "task": "Write a function to reverse a string",
            "category": "algorithms"
        }
    )
    assert response.status_code == 202
    assert "benchmark_id" in response.json()
