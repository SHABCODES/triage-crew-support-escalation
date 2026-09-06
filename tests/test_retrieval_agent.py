from app.agents.retrieval_agent import create_retrieval_agent, create_retrieval_task
from app.schemas import RetrievalOutput

def test_retrieval_agent_creation():
    agent = create_retrieval_agent()
    assert agent.role == "Knowledge Base Researcher"
    assert len(agent.tools) == 1
    assert agent.tools[0].name == "ChromaDB Retriever Tool"

def test_retrieval_task_creation():
    agent = create_retrieval_agent()
    task = create_retrieval_task(agent, "Subj", "Body", "Billing")
    assert task.output_pydantic == RetrievalOutput
    assert "Billing" in task.description
