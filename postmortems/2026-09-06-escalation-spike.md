# Incident Postmortem: Spike in Unnecessary Billing Escalations

**Date:** September 6, 2026
**Incident Commander:** [Your Name]
**Status:** Resolved
**Severity:** SEV-3
**Tools Used:** Datadog, LangSmith, Rootly

## 1. Summary
At approximately 14:00 UTC, a Datadog monitor triggered an alert indicating a sudden spike in the escalation rate of the Support Triage Crew. The auto-resolve rate plummeted, and human support agents were flooded with billing-related tickets. The incident was investigated using LangSmith traces and Datadog APM, revealing that a strict guardrail rule (`always_escalate_billing`) was aggressively catching benign billing inquiries that the Resolution Agent was otherwise fully capable of handling.

## 2. Detection
- **14:00 UTC:** Datadog monitor `[triagecrew] High Escalation Rate` fired (Threshold: > 80% escalations over 5 minutes).
- **14:02 UTC:** Incident automatically opened in Rootly via Slack integration.
- **14:05 UTC:** Incident Commander acknowledged and began investigation.

## 3. Investigation & Root Cause
- Checked Datadog APM traces for `POST /tickets`. The endpoint was returning 201s, indicating no hard crashes, but the `final_result` payloads consistently showed `decision: escalate`.
- Pulled the exact `ticket_id` of a recent escalation and cross-referenced the trace ID in LangSmith.
- **LangSmith Trace Analysis:**
  - **Triage Agent:** Correctly identified the ticket category as `Billing`.
  - **Retrieval Agent:** Successfully retrieved the refund policy from ChromaDB with high confidence.
  - **Resolution Agent:** Successfully drafted a highly accurate, grounded response explaining the prorated refund policy.
  - **Supervisor Agent (Guardrail Engine):** Despite the high confidence and grounded response, the `guardrail_rule_engine` tool forced an escalation.
- **Root Cause:** The deterministic Python rule engine (`app/guardrails/rules.py`) contains a hardcoded rule: `always_escalate_billing`. Any ticket categorized as "Billing" by the Triage Agent is instantly escalated, overriding the AI's ability to auto-resolve simple billing inquiries.

## 4. Resolution
- **14:20 UTC:** Pushed a hotfix to `app/guardrails/rules.py` to modify the `always_escalate_billing` rule. It now allows auto-resolution for "Billing" tickets if the Resolution Agent's `confidence` score is > 0.85 and the response is marked as `grounded`.
- **14:35 UTC:** Hotfix deployed to Kubernetes cluster via `kubectl rollout restart deployment triagecrew-app`.
- **14:40 UTC:** Monitored Datadog dashboard. Escalation rates normalized back to baseline (~20%).
- **14:45 UTC:** Incident resolved in Rootly.

## 5. Action Items
1. **Refine Guardrails:** Review the remaining deterministic guardrails to ensure they don't overly restrict high-confidence AI resolutions. (Owner: TBD)
2. **Alert Tuning:** Adjust the Datadog escalation alert to require a sustained spike over 10 minutes rather than 5 minutes to prevent noise from small bursts of tickets. (Owner: TBD)
3. **Knowledge Base Update:** Add more specific billing scenarios (e.g., mid-month cancellations) to the ChromaDB vector store to further increase Resolution Agent confidence. (Owner: TBD)
