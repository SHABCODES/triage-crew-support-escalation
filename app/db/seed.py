import json
import os
from sqlalchemy.orm import Session
from .session import engine, SessionLocal
from .models import Ticket, Base
from app.rag.vector_store import vector_store

def init_db():
    # Create all tables in the database
    Base.metadata.create_all(bind=engine)

def seed_tickets(db: Session, json_path: str):
    if not os.path.exists(json_path):
        print(f"File {json_path} not found.")
        return

    with open(json_path, "r") as f:
        tickets_data = json.load(f)
    
    # Check if we already seeded
    if db.query(Ticket).first():
        print("Tickets already seeded. Skipping.")
        return

    for item in tickets_data:
        ticket = Ticket(
            subject=item.get("subject"),
            body=item.get("body"),
            customer_id=item.get("customer_id")
        )
        db.add(ticket)
    
    db.commit()
    print(f"Seeded {len(tickets_data)} tickets into the database.")

if __name__ == "__main__":
    init_db()
    vector_store.load_documents()
    db = SessionLocal()
    try:
        # We assume we are running from the root directory
        seed_tickets(db, "data/synthetic_tickets.json")
    finally:
        db.close()
