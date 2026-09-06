import pytest
from unittest.mock import patch, MagicMock
from app.agents.crew import run_triage_crew

@patch("app.agents.crew.Crew.kickoff")
def test_crew_integration_mocked(mock_kickoff):
    # Mock the return value of kickoff
    mock_result = MagicMock()
    mock_result.json_dict = {
        "decision": "auto_resolve",
        "reason": "Test",
        "matched_rule": "default_auto_resolve"
    }
    mock_kickoff.return_value = mock_result
    
    mock_db = MagicMock()
    
    result = run_triage_crew(1, "Test Subject", "Test Body", mock_db)
    
    assert "final_result" in result
    assert result["final_result"]["decision"] == "auto_resolve"
