import json
from crewai import Crew, Process
from crewai.tasks.task_output import TaskOutput
from sqlalchemy.orm import Session
from app.db.models import AgentStep
from app.agents.triage_agent import create_triage_agent, create_triage_task
from app.agents.retrieval_agent import create_retrieval_agent, create_retrieval_task
from app.agents.resolution_agent import create_resolution_agent, create_resolution_task
from app.agents.supervisor_agent import create_supervisor_agent_with_tool, create_supervisor_task
from app.observability import emit_agent_step_metric, emit_final_decision_metric

def run_triage_crew(ticket_id: int, subject: str, body: str, db: Session) -> dict:
    triage_agent = create_triage_agent()
    retrieval_agent = create_retrieval_agent()
    resolution_agent = create_resolution_agent()
    supervisor_agent = create_supervisor_agent_with_tool()
    
    # We will pass the ticket details to the tasks.
    # However, for sequential process, subsequent tasks just get the context of previous tasks.
    # We can also dynamically formulate the inputs for each step, but CrewAI handles context interpolation well if we use it.
    # Since we need strict control and logging, maybe we can run them in a custom loop? 
    # TDD says: "CrewAI Process.sequential for MVP". So we must use CrewAI's Crew.
    
    # To pass outputs explicitly without relying on black-box context passing, 
    # we can define tasks that don't depend entirely on implicit context but that's hard in CrewAI sequential.
    # Actually, CrewAI sequential passes the output of Task N to Task N+1 automatically.
    # Let's define the tasks. Since we need to construct tasks dynamically based on previous outputs,
    # CrewAI might struggle with strict Pydantic parsing if the prompt just says "here is context".
    
    # To guarantee FR6 and TDD, let's run them explicitly step by step using crew.kickoff() isn't strictly required to be single-shot, but TDD says:
    # "Orchestration (agents/crew.py): CrewAI Process.sequential for MVP: Triage -> Retrieval -> Resolution -> Supervisor... Each step's raw output is persisted to the DB"
    
    trace = []
    
    def task_callback(task_output: TaskOutput):
        # We save this to DB
        step = AgentStep(
            ticket_id=ticket_id,
            agent_name=task_output.agent,
            input_json=task_output.description,
            output_json=task_output.raw
        )
        db.add(step)
        db.commit()
        trace.append({
            "agent_name": task_output.agent,
            "output": task_output.json_dict or task_output.raw
        })
        emit_agent_step_metric(task_output.agent)

    triage_task = create_triage_task(triage_agent, subject, body)
    
    # Because retrieval needs the category from triage, we can't easily define retrieval_task before triage runs if we strictly need the parsed 'category'.
    # CrewAI in Process.sequential expects all tasks to be defined upfront. 
    # We can use `{category}` in the task description if we know it, but CrewAI's string interpolation isn't native for task outputs unless we use state/kickoff inputs.
    # Actually, if we define it like this:
    retrieval_task = create_retrieval_task(retrieval_agent, subject, body, "The category determined by the previous task")
    
    resolution_task = create_resolution_task(resolution_agent, subject, body, "The category determined by the triage task", "The chunks retrieved by the retrieval task")
    
    supervisor_task = create_supervisor_task(supervisor_agent, subject + "\n" + body, "Category from triage", "Urgency from triage", 0.0, False, "Draft response from resolution task")

    # In CrewAI, setting context explicitly:
    retrieval_task.context = [triage_task]
    resolution_task.context = [triage_task, retrieval_task]
    supervisor_task.context = [triage_task, retrieval_task, resolution_task]

    crew = Crew(
        agents=[triage_agent, retrieval_agent, resolution_agent, supervisor_agent],
        tasks=[triage_task, retrieval_task, resolution_task, supervisor_task],
        process=Process.sequential,
        task_callback=task_callback,
        verbose=True
    )
    
    result = crew.kickoff()
    
    # After kickoff, the final output should be the supervisor's decision.
    final_result = result.json_dict
    
    if not final_result and result.raw:
        import re
        raw_str = result.raw
        try:
            # Strip markdown json blocks if present
            if "```json" in raw_str:
                raw_str = raw_str.split("```json")[1].split("```")[0]
            final_result = json.loads(raw_str.strip())
        except (json.JSONDecodeError, IndexError, ValueError):
            final_result = {}
    if isinstance(final_result, dict):
        decision = final_result.get("decision", "unknown")
        matched_rule = final_result.get("matched_rule", "unknown")
        emit_final_decision_metric(decision, matched_rule)

    # Return the trace and final result
    return {
        "final_result": final_result,
        "trace": trace
    }
