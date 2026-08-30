# AGENTS.md — Build Instructions for AI Coding Assistant

This file is written directly for whichever AI coding assistant (Claude Code, Cursor, etc.) implements this project. Read `PRD.md` and `TDD.md` first — this file governs *how* to build, not *what* to build.

---

## 1. Ground Rules

1. **Follow `TDD.md` exactly for architecture, file structure, and data models.** Do not introduce new top-level frameworks (no LangGraph, no AutoGen, no Semantic Kernel) — the entire point of this project is a clean, defensible CrewAI story. Mixing frameworks weakens it.
2. **Never fabricate test results, benchmark numbers, or eval metrics.** If something doesn't pass or a metric is poor, report it plainly — this project's owner has an established standard of documenting honest/null results rather than hiding them. Do not "adjust" a metric to look better.
3. **Every agent's structured output must be validated in code (Pydantic), not just trusted from the LLM.** Where `TDD.md` says a value "must" come from a fixed enum or be enforced, write an actual validation/retry path — do not implement it as a comment or a prompt instruction alone.
4. **The guardrail rule engine (`guardrails/rules.py`) must contain zero LLM calls.** It is pure Python logic. This is a hard requirement, not a preference — it's the core interview artifact.
5. **Build incrementally and get each layer working before moving to the next**, in this order:
   1. DB models + seed script
   2. ChromaDB knowledge base loading + retrieval tool (test retrieval in isolation before touching agents)
   3. Guardrail rule engine + its full test suite (no LLM dependency — get this rock-solid first)
   4. Individual agents, one at a time, each with its own test
   5. Crew orchestration wiring them together
   6. FastAPI routes + auth middleware
   7. Docker + CI last, once the app runs locally

---

## 2. Coding Conventions

- Python 3.11+, type hints everywhere, Pydantic v2 for schemas.
- Async FastAPI routes; agent/crew calls can be sync-wrapped if CrewAI's execution model requires it — don't force async where the library doesn't support it, document the boundary instead.
- Keep agent prompt/backstory text in the agent definition files (`agents/*.py`), not scattered in config — one clear place to look per agent.
- No hardcoded API keys, model names as magic strings, or file paths — pull from `config.py` (pydantic `BaseSettings`).
- Every new module gets a corresponding test file before being considered done — this project's standard bar is 25+ passing tests (see `TDD.md` §9); do not fall short of this without flagging it explicitly to the user.
- Commit messages and PR-style structure: small, logical commits (seed data, retrieval layer, guardrails, agents, API, docker/CI) rather than one giant commit — matches the reviewable-history standard of prior projects.

---

## 3. What "Done" Means (Definition of Done)

A feature/module is done only when **all** of the following are true:
- [ ] Code implements exactly what `TDD.md` specifies for that component (no silent scope changes — flag proposed deviations to the user instead of deciding unilaterally)
- [ ] Tests exist and pass for it
- [ ] It runs via `docker compose up` end to end (once integration is reached)
- [ ] Any limitation or shortcut taken is written into the README's "Honest Limitations" section (per `TDD.md` §11) — do not let shortcuts go undocumented
- [ ] No secrets committed; `.env.example` kept up to date with any new required variable

---

## 4. Explicit Non-Goals (do not build these even if it seems easy)

- No user authentication/login system beyond the single API key middleware.
- No multi-tenant data isolation.
- No fine-tuning or model training of any kind.
- No production task queue / async job system (document as a known simplification instead).
- No frontend framework (React/Vue) — Swagger UI via FastAPI is sufficient for MVP; a stretch-goal minimal HTML page is plain HTML/JS only if attempted at all.

---

## 5. When Blocked or Ambiguous

If a requirement in `PRD.md`/`TDD.md` is ambiguous, unresolvable, or conflicts with something else in the docs:
1. Do not guess silently and proceed with a large architectural decision.
2. State the ambiguity plainly and propose the smallest reasonable resolution.
3. Prefer the simpler / more explainable option over the more "impressive-sounding" one — this project is being built to be defended verbally in an interview, so implementation clarity outranks cleverness.

---

## 6. README Requirements (final deliverable checklist)

The README must include, at minimum:
- One-paragraph project summary and why it exists (support triage/escalation use case)
- Architecture diagram (Mermaid or ASCII) matching `TDD.md` §5-6
- Setup instructions (clone → `.env` → `docker compose up`) that work on a clean machine
- A worked example: one sample ticket in, full response out, shown in the README
- Test coverage summary (how many tests, what they cover)
- **Honest Limitations** section (per `TDD.md` §11) — non-negotiable, must be present
- A short "What I'd do differently at enterprise scale" section — this is a strong interview talking point and should be written thoughtfully, not boilerplate
