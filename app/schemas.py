from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class CategoryEnum(str, Enum):
    Billing = "Billing"
    Technical = "Technical"
    Account = "Account"
    General = "General"

class UrgencyEnum(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"

class DecisionEnum(str, Enum):
    auto_resolve = "auto_resolve"
    escalate = "escalate"

class TicketCreate(BaseModel):
    subject: str
    body: str
    customer_id: Optional[str] = None

class TriageOutput(BaseModel):
    category: CategoryEnum = Field(..., description="The categorized bucket for the ticket.")
    urgency: UrgencyEnum = Field(..., description="The determined urgency level.")
    rationale: str = Field(..., description="Explanation for why this category and urgency were chosen.")

class RetrievedChunk(BaseModel):
    text: str
    source: str
    score: float

class RetrievalOutput(BaseModel):
    retrieved_chunks: List[RetrievedChunk] = Field(..., description="The top retrieved relevant knowledge chunks.")
    low_relevance: bool = Field(False, description="True if the retrieved chunks have low relevance scores (e.g. below 0.3).")

class ResolutionOutput(BaseModel):
    draft_response: str = Field(..., description="The drafted response to the customer.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0.")
    reasoning: str = Field(..., description="The reasoning behind the drafted response.")
    grounded: bool = Field(..., description="Whether the response is fully grounded in the retrieved knowledge base.")

class SupervisorOutput(BaseModel):
    decision: DecisionEnum = Field(..., description="Whether to auto-resolve or escalate the ticket.")
    reason: str = Field(..., description="Explanation for the decision.")
    matched_rule: str = Field(..., description="The specific guardrail rule that triggered this decision.")
