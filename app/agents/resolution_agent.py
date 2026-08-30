from crewai import Agent, Task
from app.schemas import ResolutionOutput

def create_resolution_agent() -> Agent:
    return Agent(
        role="Response Drafter",
        goal="Draft a customer-facing response grounded ONLY in retrieved context, or state that it cannot answer.",
        backstory="You are a professional customer support agent. You write clear, polite, and helpful responses to customers based strictly on the company's knowledge base. If you don't have enough information from the knowledge base, you do not guess or hallucinate.",
        verbose=True,
        allow_delegation=False,
    )

def create_resolution_task(agent: Agent, ticket_subject: str, ticket_body: str, category: str, retrieved_chunks: str) -> Task:
    return Task(
        description=f"Draft a response for this ticket.\n\nTicket Subject: {ticket_subject}\nTicket Body: {ticket_body}\nCategory: {category}\n\nRetrieved Knowledge:\n{retrieved_chunks}\n\nInstructions:\n1. If retrieved chunks are empty or irrelevant, you must set grounded to false and confidence to <= 0.3.\n2. Do not hallucinate facts outside the retrieved knowledge.\n3. Output must be a valid JSON matching ResolutionOutput.",
        expected_output="A JSON object conforming to the ResolutionOutput schema.",
        agent=agent,
        output_pydantic=ResolutionOutput
    )
