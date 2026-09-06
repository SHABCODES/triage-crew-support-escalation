from app.agents.resolution_agent import create_resolution_agent, create_resolution_task
from app.schemas import ResolutionOutput

def test_resolution_agent_creation():
    agent = create_resolution_agent()
    assert agent.role == "Response Drafter"

def test_resolution_task_creation():
    agent = create_resolution_agent()
    task = create_resolution_task(agent, "Subj", "Body", "Billing", "chunk text")
    assert task.output_pydantic == ResolutionOutput
    assert "chunk text" in task.description
