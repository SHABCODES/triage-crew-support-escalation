import pytest
from app.guardrails.rules import SupervisorInput, evaluate_guardrails

def test_always_escalate_billing():
    data = SupervisorInput(
        category="Billing",
        urgency="Low",
        confidence=0.9,
        grounded=True,
        draft_response="Here is your refund.",
        ticket_text="Can I get a refund?"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "escalate"
    assert rule == "always_escalate_billing"

def test_sensitive_keyword_match():
    data = SupervisorInput(
        category="Account",
        urgency="Low",
        confidence=0.9,
        grounded=True,
        draft_response="I understand you want a refund...",
        ticket_text="I will file a lawsuit if you don't cancel my account."
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "escalate"
    assert rule == "sensitive_keyword_match"

def test_ungrounded_response():
    data = SupervisorInput(
        category="Technical",
        urgency="Low",
        confidence=0.9,
        grounded=False,
        draft_response="I don't know, maybe check the docs?",
        ticket_text="How to fix this?"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "escalate"
    assert rule == "ungrounded_response"

def test_low_confidence():
    data = SupervisorInput(
        category="Technical",
        urgency="Low",
        confidence=0.5, # < 0.6
        grounded=True,
        draft_response="I think it's this.",
        ticket_text="How to fix?"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "escalate"
    assert rule == "low_confidence"

def test_high_urgency_low_confidence():
    data = SupervisorInput(
        category="Technical",
        urgency="High",
        confidence=0.7, # < 0.8 for High urgency
        grounded=True,
        draft_response="Maybe this helps.",
        ticket_text="CRITICAL OUTAGE"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "escalate"
    assert rule == "high_urgency_low_confidence"

def test_default_auto_resolve():
    data = SupervisorInput(
        category="Technical",
        urgency="Medium",
        confidence=0.85,
        grounded=True,
        draft_response="Here is the exact solution from the docs.",
        ticket_text="How do I setup webhooks?"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "auto_resolve"
    assert rule == "default_auto_resolve"

def test_high_urgency_high_confidence():
    data = SupervisorInput(
        category="Technical",
        urgency="High",
        confidence=0.9,
        grounded=True,
        draft_response="Here is the fix.",
        ticket_text="Fix this now!"
    )
    decision, rule = evaluate_guardrails(data)
    assert decision == "auto_resolve"
    assert rule == "default_auto_resolve"
