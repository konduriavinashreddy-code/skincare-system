import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.seed import seed_products

@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    def override_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_db
    with TestingSession() as session:
        seed_products(session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)

@pytest.fixture
def account(client):
    response = client.post("/api/auth/register", json={"full_name": "Test User", "email": "test@example.com", "password": "long-test-password"})
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}