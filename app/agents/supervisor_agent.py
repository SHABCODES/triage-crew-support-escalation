from crewai import Agent, Task
from app.schemas import SupervisorOutput

def create_supervisor_agent() -> Agent:
    return Agent(
        role="Escalation Supervisor",
        goal="Apply the deterministic rule set to decide resolve vs. escalate.",
        backstory="You are a strict supervisor. Your only job is to look at the ticket data, the drafted response, the confidence, and the urgency, and apply a deterministic set of guardrail rules to decide whether to escalate to a human or auto-resolve.",
        verbose=True,
        allow_delegation=False,
    )

def create_supervisor_task(agent: Agent, ticket_text: str, category: str, urgency: str, confidence: float, grounded: bool, draft_response: str) -> Task:
    # Instead of an LLM making the decision entirely on its own based on vague prompts, 
    # we enforce the python rule engine here as the primary logic, and wrap the agent to just 
    # output the structured result, or we can use a custom tool.
    # The TDD states: "Tools: guardrail_rule_engine (this is a code function, not an LLM call)"
    # However, CrewAI tasks run through the agent. 
    # Let's provide the agent with a tool to evaluate guardrails, or just compute it before the agent and have the agent report it?
    # TDD says: "Supervisor Agent must apply a documented, deterministic rule set... mostly a wrapper around deterministic code."
    
    # We will pass the evaluated result into the prompt and just ask the agent to format it!
    # Wait, if we just pass the evaluated result, the agent doesn't do any thinking. 
    # Let's create a tool for the agent to call the guardrails, OR evaluate it and inject it into the task.
    # Creating a tool is better.
    
    return Task(
        description=f"You must use the guardrail rule engine to determine if this ticket should be escalated.\n\nTicket Text: {ticket_text}\nCategory: {category}\nUrgency: {urgency}\nConfidence: {confidence}\nGrounded: {grounded}\nDraft Response: {draft_response}\n\nCall the guardrail_rule_engine tool with these precise parameters to get the decision and rule name. Then output the final JSON.",
        expected_output="A JSON object conforming to the SupervisorOutput schema.",
        agent=agent,
        output_pydantic=SupervisorOutput
    )

from crewai.tools import tool
from app.guardrails.rules import evaluate_guardrails, SupervisorInput

@tool("Guardrail Rule Engine")
def guardrail_rule_engine_tool(category: str, urgency: str, confidence: float, grounded: bool, draft_response: str, ticket_text: str) -> str:
    """
    Evaluates the ticket data against deterministic rules.
    Input parameters: category, urgency, confidence, grounded, draft_response, ticket_text.
    Returns the decision and matched rule.
    """
    inp = SupervisorInput(
        category=category,
        urgency=urgency,
        confidence=confidence,
        grounded=grounded,
        draft_response=draft_response,
        ticket_text=ticket_text
    )
    decision, matched_rule = evaluate_guardrails(inp)
    return f"Decision: {decision}, Matched Rule: {matched_rule}"

# To give the tool to the agent:
def create_supervisor_agent_with_tool() -> Agent:
    agent = create_supervisor_agent()
    agent.tools = [guardrail_rule_engine_tool]
    return agent
