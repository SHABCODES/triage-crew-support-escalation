from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Ticket, Resolution
from app.schemas import TicketCreate
from app.agents.crew import run_triage_crew
import json

router = APIRouter(prefix="/tickets", tags=["tickets"])

@router.post("", status_code=201)
def create_ticket(ticket_data: TicketCreate, db: Session = Depends(get_db)):
    # Create ticket in DB
    ticket = Ticket(
        subject=ticket_data.subject,
        body=ticket_data.body,
        customer_id=ticket_data.customer_id,
        status="processing"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    # Process synchronously for MVP
    try:
        result = run_triage_crew(ticket.id, ticket.subject, ticket.body, db)
        
        # Save resolution
        final_result = result.get("final_result", {})
        resolution = Resolution(
            ticket_id=ticket.id,
            decision=final_result.get("decision", "escalate"),
            matched_rule=final_result.get("matched_rule", "unknown"),
            draft_response=final_result.get("draft_response"),
            confidence=final_result.get("confidence"),
            reason=final_result.get("reason", "Unknown")
        )
        db.add(resolution)
        
        # Update ticket category and urgency from trace
        for step in result.get("trace", []):
            if step["agent_name"] == "Support Ticket Classifier" and step.get("output"):
                out = step["output"]
                if isinstance(out, dict):
                    ticket.category = out.get("category")
                    ticket.urgency = out.get("urgency")
                elif isinstance(out, str):
                    try:
                        parsed = json.loads(out)
                        ticket.category = parsed.get("category")
                        ticket.urgency = parsed.get("urgency")
                    except json.JSONDecodeError:
                        pass
        
        # Update ticket status
        ticket.status = "resolved" if resolution.decision == "auto_resolve" else "escalated"
        db.commit()
    except Exception as e:  # noqa: BLE001
        ticket.status = "escalated"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"id": ticket.id, "status": ticket.status}

@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    agent_trace = []
    for step in ticket.agent_steps:
        agent_trace.append({
            "agent_name": step.agent_name,
            "output": step.output_json
        })
        
    res = ticket.resolution
    resolution_data = None
    if res:
        resolution_data = {
            "decision": res.decision,
            "matched_rule": res.matched_rule,
            "draft_response": res.draft_response,
            "confidence": res.confidence,
            "reason": res.reason
        }
        
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "body": ticket.body,
        "status": ticket.status,
        "category": ticket.category,
        "urgency": ticket.urgency,
        "agent_trace": agent_trace,
        "resolution": resolution_data
    }

@router.get("")
def list_tickets(status: str = Query(None), db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
        
    tickets = query.limit(50).all()
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "category": t.category,
            "urgency": t.urgency
        } for t in tickets
    ]
