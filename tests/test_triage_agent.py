from app.agents.triage_agent import create_triage_agent, create_triage_task
from app.schemas import TriageOutput

def test_triage_agent_creation():
    agent = create_triage_agent()
    assert agent.role == "Support Ticket Classifier"
    assert agent.allow_delegation is False

def test_triage_task_creation():
    agent = create_triage_agent()
    task = create_triage_task(agent, "Subject", "Body")
    assert task.agent == agent
    assert task.output_pydantic == TriageOutput
    assert "Subject" in task.description
