from crewai import Agent, Task
from app.schemas import TriageOutput

def create_triage_agent() -> Agent:
    return Agent(
        role="Support Ticket Classifier",
        goal="Assign exactly one category and one urgency level to an incoming ticket.",
        backstory="You are an expert IT and support triage specialist. You quickly and accurately route incoming customer issues based on their content. You only choose from the allowed categories and urgencies.",
        verbose=True,
        allow_delegation=False,
    )

def create_triage_task(agent: Agent, ticket_subject: str, ticket_body: str) -> Task:
    return Task(
        description=f"Classify the following support ticket.\n\nSubject: {ticket_subject}\nBody: {ticket_body}\n\nDetermine the category (Billing, Technical, Account, General) and urgency (Low, Medium, High).",
        expected_output="A JSON object conforming to the TriageOutput schema.",
        agent=agent,
        output_pydantic=TriageOutput
    )
