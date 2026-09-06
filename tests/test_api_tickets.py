import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from unittest.mock import patch

client = TestClient(app)
headers = {"X-API-Key": settings.api_key}

@patch("app.routers.tickets.run_triage_crew")
def test_create_ticket(mock_run_triage_crew):
    mock_run_triage_crew.return_value = {
        "final_result": {
            "decision": "auto_resolve",
            "matched_rule": "default_auto_resolve",
            "draft_response": "Hello",
            "confidence": 0.9,
            "reason": "Clear"
        },
        "trace": []
    }
    
    response = client.post("/tickets", json={"subject": "Test", "body": "Testing 123"}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "resolved"

def test_get_ticket_not_found():
    response = client.get("/tickets/99999", headers=headers)
    assert response.status_code == 404

def test_list_tickets():
    response = client.get("/tickets", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
