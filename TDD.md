# TDD — TriageCrew: Technical Design Document

Companion to `PRD.md`. This document is the implementation blueprint — an AI coding assistant or Shabda herself should be able to build directly from this without re-deriving design decisions.

---

## 1. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Agent orchestration | **CrewAI** | pin version in `requirements.txt`; primary named-framework requirement being demonstrated |
| LLM tool-calling glue (retrieval tool) | **LangChain** (retriever wrapper only) | reuse of existing skill; CrewAI can call LangChain tools directly |
| Vector store | **ChromaDB** | local persistent client, no external service dependency |
| LLM provider | OpenAI API (configurable via env var) | documented as swappable; local-model swap is a stretch goal, not MVP |
| Backend API | **FastAPI** (async) | matches existing pattern |
| ORM / DB | **SQLAlchemy** + **SQLite** | SQLite chosen for zero-friction reviewer setup (see PRD §10) |
| Auth | API key middleware (header-based) | reuse pattern from intelligent-form-agent |
| Testing | **pytest** | target 25+ tests |
| Containerization | **Docker** + `docker-compose.yml` | single command startup |
| CI | **GitHub Actions** | lint + test on push/PR |

---

## 2. Repository Structure

```
triagecrew/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # env/config loading (pydantic settings)
│   ├── auth.py                  # API key middleware
│   ├── db/
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── session.py            # DB session/engine setup
│   │   └── seed.py               # seeds tickets + KB corpus
│   ├── agents/
│   │   ├── crew.py               # CrewAI Crew + Process definition
│   │   ├── triage_agent.py
│   │   ├── retrieval_agent.py
│   │   ├── resolution_agent.py
│   │   └── supervisor_agent.py
│   ├── guardrails/
│   │   └── rules.py              # deterministic escalation rule engine (FR5/FR8)
│   ├── rag/
│   │   ├── vector_store.py       # ChromaDB client + collection setup
│   │   └── knowledge_base/       # source .md/.txt policy & FAQ docs (synthetic)
│   ├── schemas.py                # Pydantic request/response models
│   └── routers/
│       └── tickets.py            # FR1, FR6, FR7 endpoints
├── data/
│   └── synthetic_tickets.json    # labeled synthetic ticket dataset (for eval, FR10)
├── tests/
│   ├── test_triage_agent.py
│   ├── test_retrieval_agent.py
│   ├── test_resolution_agent.py
│   ├── test_supervisor_guardrails.py
│   ├── test_crew_integration.py
│   ├── test_api_tickets.py
│   └── test_auth.py
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Agent Specifications

Each agent is defined as a CrewAI `Agent` with an explicit `role`, `goal`, `backstory` (kept factual/functional, not flowery), a bounded tool list, and — critically — a stated **input/output contract** so behavior is testable, not just "vibes."

### 3.1 Triage Agent

- **Role:** Support Ticket Classifier
- **Goal:** Assign exactly one category and one urgency level to an incoming ticket.
- **Tools:** none (pure classification via LLM reasoning over ticket text)
- **Input:** `{subject: str, body: str}`
- **Output (structured):** `{category: Enum[Billing, Technical, Account, General], urgency: Enum[Low, Medium, High], rationale: str}`
- **Guardrail note:** category/urgency **must** come from a fixed enum — reject/retry if the LLM returns anything outside the set. This is a concrete, demonstrable guardrail (schema-level enforcement, not just prompt instruction).

### 3.2 Retrieval Agent

- **Role:** Knowledge Base Researcher
- **Goal:** Find the most relevant policy/FAQ passages for a given ticket + category.
- **Tools:** `chroma_retriever_tool` (wraps a ChromaDB similarity search, top_k configurable, default 3)
- **Input:** `{subject: str, body: str, category: str}`
- **Output:** `{retrieved_chunks: List[{text: str, source: str, score: float}]}`
- **Guardrail note:** if similarity score of top result is below a defined floor (e.g., 0.3), agent must return `retrieved_chunks: []` and flag `low_relevance: true` rather than force-feeding irrelevant context downstream — this becomes an input to the Supervisor's escalation decision.

### 3.3 Resolution Agent

- **Role:** Response Drafter
- **Goal:** Draft a customer-facing response grounded only in retrieved context, or state that it cannot answer.
- **Tools:** none (uses retrieved_chunks passed in context, does not re-query)
- **Input:** `{subject: str, body: str, category: str, retrieved_chunks: List[...]}`
- **Output:** `{draft_response: str, confidence: float (0-1), reasoning: str, grounded: bool}`
- **Guardrail note:** if `retrieved_chunks` is empty, agent must set `grounded: false` and `confidence <= 0.3` by construction (enforced in prompt **and** validated post-hoc in code — do not trust the LLM to self-report honestly without a code-level check).

### 3.4 Supervisor Agent (Escalation Decision)

- **Role:** Escalation Supervisor
- **Goal:** Apply the deterministic rule set in `guardrails/rules.py` to decide resolve vs. escalate.
- **Tools:** `guardrail_rule_engine` (this is a **code function**, not an LLM call — see §4)
- **Input:** `{category, urgency, confidence, grounded, draft_response, ticket_text}`
- **Output:** `{decision: Enum[auto_resolve, escalate], reason: str, matched_rule: str}`
- **Design decision:** This agent is intentionally the *thinnest* — it should mostly be a wrapper around deterministic code, not free LLM judgment, because escalation correctness is the part of the system that must be auditable and explainable in an interview.

---

## 4. Guardrail Rule Engine (`guardrails/rules.py`)

This is the artifact to walk an interviewer through directly. Rules evaluated in order, first match wins:

```python
RULES = [
    # (rule_name, condition_fn, decision)
    ("always_escalate_billing", lambda t: t.category == "Billing", "escalate"),
    ("sensitive_keyword_match", lambda t: contains_flagged_keywords(t.ticket_text), "escalate"),
    ("ungrounded_response", lambda t: not t.grounded, "escalate"),
    ("low_confidence", lambda t: t.confidence < 0.6, "escalate"),
    ("high_urgency_low_confidence", lambda t: t.urgency == "High" and t.confidence < 0.8, "escalate"),
    ("default_auto_resolve", lambda t: True, "auto_resolve"),
]
```

`contains_flagged_keywords` checks against a documented, editable list (e.g., "cancel my account", "legal action", "refund dispute", "lawsuit", plus safety-relevant terms) stored in a plain config file, not buried in a prompt.

**This module ships with its own dedicated test file (`test_supervisor_guardrails.py`) covering every rule branch — this is the single most important test file in the project for the interview narrative.**

---

## 5. Orchestration (`agents/crew.py`)

- **CrewAI `Process.sequential`** for MVP: Triage → Retrieval → Resolution → Supervisor, each agent's output feeding the next via CrewAI's task context passing.
- Each step's raw output is persisted to the DB (see §6) regardless of what happens downstream — this is what makes `GET /tickets/{id}` return a full trace (FR6).
- Stretch goal (per PRD §9): re-run the same pipeline under `Process.hierarchical` with a manager agent and diff the behavior for a "what I learned comparing orchestration modes" README section — good interview talking point, not required for MVP.

---

## 6. Data Model (`db/models.py`)

```
Ticket
  id: int (pk)
  subject: str
  body: str
  customer_id: str (nullable)
  status: enum(pending, resolved, escalated)
  category: str (nullable until triaged)
  urgency: str (nullable until triaged)
  created_at: datetime
  updated_at: datetime

AgentStep
  id: int (pk)
  ticket_id: int (fk -> Ticket)
  agent_name: str            # "triage" | "retrieval" | "resolution" | "supervisor"
  input_json: text
  output_json: text
  created_at: datetime

Resolution
  id: int (pk)
  ticket_id: int (fk -> Ticket, unique)
  decision: str               # auto_resolve | escalate
  matched_rule: str
  draft_response: text (nullable)
  confidence: float (nullable)
  reason: text
```

`AgentStep` is what makes the system auditable (PRD FR6/FR8) — every agent's input and output is stored, not just the final answer.

---

## 7. API Contracts

### `POST /tickets`
Request:
```json
{ "subject": "string", "body": "string", "customer_id": "string (optional)" }
```
Response `201`:
```json
{ "id": 1, "status": "processing" }
```
(Processing can be synchronous for MVP — return final result directly — or return `processing` and require a follow-up GET; **recommend synchronous for MVP** to keep the demo simple, document as a known simplification vs. an async/queue-based production design.)

### `GET /tickets/{id}`
Response `200`:
```json
{
  "id": 1,
  "subject": "...",
  "body": "...",
  "status": "resolved",
  "category": "Technical",
  "urgency": "Medium",
  "agent_trace": [
    { "agent_name": "triage", "output": {...} },
    { "agent_name": "retrieval", "output": {...} },
    { "agent_name": "resolution", "output": {...} },
    { "agent_name": "supervisor", "output": {...} }
  ],
  "resolution": {
    "decision": "auto_resolve",
    "matched_rule": "default_auto_resolve",
    "draft_response": "...",
    "confidence": 0.82
  }
}
```

### `GET /tickets?status=escalated`
Returns a paginated list of ticket summaries filtered by status.

### Auth
All endpoints require header `X-API-Key: <key>`; missing/invalid key returns `401`.

---

## 8. Synthetic Data Requirements (FR10)

- `data/synthetic_tickets.json`: minimum 30 labeled tickets spanning all 4 categories and all urgency levels, hand-written or LLM-drafted-then-reviewed (must be reviewed by Shabda before use — do not ship unreviewed synthetic data, consistent with the project's honesty standard).
- `app/rag/knowledge_base/`: 15-25 short synthetic policy/FAQ documents (billing policy, account recovery steps, technical troubleshooting FAQs, general company info) — clearly marked as fictional/synthetic in a header comment in each file.
- `app/db/seed.py` loads both into SQLite + ChromaDB on first run.

---

## 9. Testing Strategy (NFR2)

| Test file | Coverage focus |
|---|---|
| `test_triage_agent.py` | Category/urgency enum enforcement, retry-on-invalid-output behavior |
| `test_retrieval_agent.py` | Correct top-k retrieval, low-relevance floor behavior |
| `test_resolution_agent.py` | Grounded/ungrounded confidence enforcement |
| `test_supervisor_guardrails.py` | Every rule branch in `RULES`, in isolation, with mocked inputs — no LLM calls needed, pure logic tests |
| `test_crew_integration.py` | End-to-end pipeline on 2-3 sample tickets (can mock LLM calls to keep CI fast/deterministic, or mark as a slower integration test) |
| `test_api_tickets.py` | POST/GET endpoint contracts, status codes, pagination/filtering |
| `test_auth.py` | Missing/invalid/valid API key behavior |

**Design principle:** guardrail logic tests must not depend on live LLM calls — that's what makes them fast, deterministic, and CI-friendly, and it's also the strongest interview point ("the safety-critical logic is unit-tested independent of model behavior").

---

## 10. Deployment

- `Dockerfile`: single-stage Python image, installs `requirements.txt`, runs `uvicorn`.
- `docker-compose.yml`: single service (app), mounts a volume for ChromaDB persistence and SQLite file.
- `.env.example` documents required vars: `OPENAI_API_KEY`, `API_KEY` (for auth middleware), `CHROMA_PERSIST_DIR`, `DATABASE_URL`.
- `.github/workflows/ci.yml`: on push/PR — install deps, run `ruff`/`flake8` lint, run `pytest` (excluding or mocking any test that requires a live API key, guarded via `pytest.mark.skipif`).

---

## 11. Honest Limitations to Document in README (per PRD NFR6)

- Confidence scores from the Resolution Agent are LLM-self-reported and heuristic, not a calibrated statistical probability — clearly label this.
- Synthetic data only; no claim of production-scale validation.
- Synchronous request handling for MVP simplicity — not how you'd design this for real production ticket volume (would need a task queue).
- Guardrail keyword list is illustrative, not exhaustive — a real system would need a maintained, larger, possibly ML-assisted flagged-term list.

---

**Next document:** See `AGENTS.md` for build conventions, definition-of-done, and instructions written directly for an AI coding assistant to follow during implementation.
