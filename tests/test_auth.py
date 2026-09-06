from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def test_missing_api_key():
    response = client.get("/tickets")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API Key"}

def test_invalid_api_key():
    response = client.get("/tickets", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401

def test_valid_api_key():
    # Because DB is empty, this should return an empty list or 200 at least
    response = client.get("/tickets", headers={"X-API-Key": settings.api_key})
    assert response.status_code == 200
