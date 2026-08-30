from dataclasses import dataclass
from typing import Tuple

FLAGGED_KEYWORDS = [
    "cancel my account", 
    "legal action", 
    "refund dispute", 
    "lawsuit", 
    "sue", 
    "chargeback"
]

@dataclass
class SupervisorInput:
    category: str
    urgency: str
    confidence: float
    grounded: bool
    draft_response: str
    ticket_text: str

def contains_flagged_keywords(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in FLAGGED_KEYWORDS)

RULES = [
    # (rule_name, condition_fn, decision)
    ("always_escalate_billing", lambda t: t.category == "Billing", "escalate"),
    ("sensitive_keyword_match", lambda t: contains_flagged_keywords(t.ticket_text), "escalate"),
    ("ungrounded_response", lambda t: not t.grounded, "escalate"),
    ("low_confidence", lambda t: t.confidence is not None and t.confidence < 0.6, "escalate"),
    ("high_urgency_low_confidence", lambda t: t.urgency == "High" and t.confidence is not None and t.confidence < 0.8, "escalate"),
    ("default_auto_resolve", lambda t: True, "auto_resolve"),
]

def evaluate_guardrails(ticket_data: SupervisorInput) -> Tuple[str, str]:
    """
    Evaluates the ticket data against deterministic rules.
    Returns (decision, matched_rule).
    """
    for rule_name, condition_fn, decision in RULES:
        if condition_fn(ticket_data):
            return decision, rule_name
            
    # Fallback (should never be reached if default_auto_resolve is present)
    return "escalate", "fallback_unknown"
