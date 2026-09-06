# PRD — TriageCrew: Multi-Agent Enterprise Support & Escalation System

**Owner:** Shabda
**Status:** Draft v1.0
**Purpose of this doc:** Define exactly what to build so it can be handed to an AI coding assistant (or built by hand) with minimal ambiguity. Every requirement below should be traceable to something demonstrable in a portfolio walkthrough or interview.

---

## 1. Problem Statement

Enterprise support teams receive high volumes of repetitive customer queries (billing, technical, account/general) that follow predictable resolution patterns, but still require judgment about *when a human must intervene*. A naive single-LLM chatbot either over-automates (answers things it shouldn't) or under-automates (escalates everything, defeating the purpose).

**This project builds a multi-agent system that mirrors how a real support organization is structured** — a triage function, a knowledge/research function, a resolution/drafting function, and a supervisor function that owns the escalate-or-resolve decision — implemented as coordinating AI agents rather than a single monolithic prompt.

This directly targets the "AI Customer Engineer" role class: building agentic systems with defined tools, reasoning, and guardrails, exposed as production-style services.

---

## 2. Goals

- **G1:** Demonstrate hands-on, defensible experience with a named multi-agent framework (CrewAI).
- **G2:** Demonstrate explicit guardrail design — not just "the LLM decided," but auditable rules for when the system will and will not act autonomously.
- **G3:** Reuse and extend existing RAG/backend skills (ChromaDB, FastAPI, SQLAlchemy) so the project reads as a natural extension of prior work, not a disconnected toy.
- **G4:** Produce something demo-able end-to-end in an interview: submit a ticket → watch agents reason → get a resolution or an escalation with a stated reason.
- **G5:** Ship with the same engineering bar as prior projects: automated tests, Docker, CI, and a real (not synthetic) evaluation dataset.

## 3. Non-Goals (explicitly out of scope for v1)

- **NG1:** No real customer data or PII — use a synthetic-but-realistic support ticket dataset (documented as such, same honesty standard as the FinQA null-result project).
- **NG2:** No fine-tuning of an LLM. This project is about **orchestration and guardrails**, not model training (that ground is already covered by the FinQA LoRA project — don't duplicate).
- **NG3:** No multi-tenant SaaS concerns (auth is a single API key, not per-tenant RLS — that's already demonstrated in Instant HelpDesk).
- **NG4:** No frontend UI beyond a minimal way to submit/view tickets (Swagger/OpenAPI docs via FastAPI is sufficient; a small HTML page is a stretch goal, not a requirement).
- **NG5:** No CoPilot Studio / Google ADK integration in v1 (separate future project if needed — mixing frameworks in one project weakens the story).

## 4. Target "User" (for framing, even though this is a portfolio project)

A mid-size enterprise's **Tier-1 Support Operations Lead** who wants to auto-resolve routine tickets while guaranteeing that billing disputes, legal/compliance-flagged language, and low-confidence answers always reach a human.

## 5. Core Use Case Walkthrough

1. A support ticket comes in (subject + body text), submitted via API.
2. **Triage Agent** classifies it: category (Billing / Technical / Account / General) + urgency (Low / Medium / High).
3. **Retrieval Agent** queries the knowledge base (ChromaDB) for relevant policy/help-doc snippets related to the ticket.
4. **Resolution Agent** drafts a proposed response using the retrieved context, and attaches a **confidence score** and **reasoning trace**.
5. **Supervisor Agent** applies guardrail rules against the category, confidence score, and content of the draft to decide: **auto-resolve** or **escalate to human**, and logs why.
6. The system returns a structured result: ticket status, category, draft response (if resolved) or escalation reason (if escalated), and the full agent reasoning trail for auditability.

## 6. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | System accepts a new support ticket via `POST /tickets` (subject, body, customer_id optional). |
| FR2 | Triage Agent must classify ticket into one of a fixed set of categories and an urgency level, and this classification must be stored, not just inferred silently. |
| FR3 | Retrieval Agent must query a ChromaDB knowledge base seeded with a documented synthetic policy/FAQ corpus and return the top-k relevant chunks used. |
| FR4 | Resolution Agent must produce a draft response **and** a numeric/qualitative confidence indicator **and** a short reasoning explanation — all three, not just the answer. |
| FR5 | Supervisor Agent must apply a documented, deterministic rule set (not just LLM judgment) for escalation — e.g., category == Billing → always escalate; confidence < threshold → escalate; flagged keywords (legal, refund dispute, cancellation threat, self-harm/safety) → always escalate regardless of confidence. |
| FR6 | Every ticket's full agent trace (who did what, in what order, with what output) must be retrievable via `GET /tickets/{id}`. |
| FR7 | System must expose a way to list all tickets and filter by status (resolved / escalated) via `GET /tickets?status=`. |
| FR8 | All guardrail rules must live in one clearly identified, human-readable config/module — not scattered across prompts — so they can be shown and explained in an interview. |
| FR9 | API must be protected by a simple API key auth middleware (reuse pattern from intelligent-form-agent). |
| FR10 | System must ship with a seed script that loads the synthetic ticket dataset and knowledge base so a reviewer can run it end-to-end from a clean clone. |

## 7. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Single ticket end-to-end processing should complete in a reasonable demo time (target: under ~20s with a standard hosted LLM API; document actual latency, don't hide it). |
| NFR2 | All agent framework, tool, and guardrail code must be covered by automated tests (target: 25+ tests, matching the bar set by prior projects). |
| NFR3 | System must run via `docker compose up` with no manual setup beyond an `.env` file for API keys. |
| NFR4 | CI (GitHub Actions) must run lint + tests on every push. |
| NFR5 | No hardcoded secrets; API keys via environment variables only. |
| NFR6 | Every honest limitation (e.g., "confidence score is heuristic, not calibrated probability") must be documented in the README, not glossed over — consistent with the project's existing standard of transparent, defensible claims. |

## 8. Success Metrics (for the README / demo narrative)

- % of synthetic test tickets correctly triaged into the right category (measured against labeled synthetic set).
- % of tickets correctly escalated per the guardrail rules (this should be ~100% since rules are deterministic — the interesting number is whether the *category/confidence inputs* to those rules were reasonable).
- Test coverage / pass count.
- End-to-end latency, honestly reported.

This mirrors the honest-evaluation standard already set by the predictive-maintenance (ROC-AUC 0.989 + baseline) and FinQA (documented null result) projects — no invented numbers.

## 9. MVP Scope vs. Stretch Goals

**MVP (required for the interview story):**
- 4 agents (Triage, Retrieval, Resolution, Supervisor) via CrewAI, sequential process
- ChromaDB-backed RAG with a synthetic FAQ/policy corpus (~30-50 documents)
- FastAPI service with the endpoints in FR1/FR6/FR7
- Deterministic guardrail rule module
- Docker + docker-compose + GitHub Actions CI
- Test suite (pytest)
- README with architecture diagram (ASCII or Mermaid is fine), setup instructions, and honest limitations section

**Stretch (only if time allows, do not let these delay MVP):**
- Minimal HTML/Streamlit page to submit tickets and view the agent trace visually
- Swap `Process.sequential` for `Process.hierarchical` in CrewAI and compare behavior
- Add a second knowledge base "freshness" agent that flags stale docs
- Deploy to a free-tier cloud host (Render/Fly.io) to also touch the cloud-exposure gap

## 10. Assumptions & Open Questions

- **Assumption:** Uses a hosted LLM API (OpenAI or similar) rather than local models, for demo reliability and speed — should be documented as a deliberate choice, with a note that a local-model swap is architecturally possible given prior local-model experience.
- **Open question:** Which LLM provider/API key does Shabda want to use for build/test? (Needed before implementation starts.)
- **Open question:** Should ticket data persist in SQLite (simple, portfolio-friendly) or PostgreSQL (matches production pattern used in intelligent-form-agent)? Recommendation: SQLite for this project to keep setup friction near zero for reviewers, documented as a swappable choice.

## 11. Risks

| Risk | Mitigation |
|------|-----------|
| CrewAI API changes/version drift | Pin exact version in requirements; document version in README |
| LLM non-determinism makes demo unpredictable | Use low temperature for classification/guardrail-relevant steps; keep a recorded demo run/GIF as backup |
| Guardrail rules look "too simple" to be impressive | Frame correctly in interviews: the point is *auditability and control*, not rule complexity — this is the actual enterprise concern |
| Scope creep into a second framework (ADK/AutoGen) | Explicitly out of scope per NG5 — resist mid-build |

---

**Next document:** See `TDD.md` for architecture, agent specs, data models, and API contracts. See `AGENTS.md` for coding conventions and definition-of-done, written for direct use by an AI coding assistant during implementation.
