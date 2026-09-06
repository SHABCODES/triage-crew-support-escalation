from fastapi import FastAPI, Depends
from app.routers import tickets
from app.auth import get_api_key
from app.db.session import engine
from app.db.models import Base
from app.observability import init_langsmith_tracing

# Create tables if not exists
Base.metadata.create_all(bind=engine)

# Initialize observability
init_langsmith_tracing()

app = FastAPI(
    title="TriageCrew API",
    description="Multi-Agent Enterprise Support & Escalation System",
    version="1.0.0",
    dependencies=[Depends(get_api_key)]
)

app.include_router(tickets.router)

@app.get("/health", dependencies=[])
def health_check():
    return {"status": "ok"}
