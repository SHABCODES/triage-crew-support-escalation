import os
from datadog import initialize, statsd
import litellm

def init_langsmith_tracing():
    """Initializes LangSmith tracing if the API key is present."""
    if os.environ.get("LANGSMITH_API_KEY"):
        # LiteLLM natively supports LangSmith/Langfuse and others via callbacks
        litellm.success_callback = ["langsmith"]
        litellm.failure_callback = ["langsmith"]
        print("LangSmith tracing initialized via LiteLLM.")

# Initialize Datadog statsd client if api key is present
if os.environ.get("DD_API_KEY"):
    options = {
        'statsd_host': os.environ.get('DD_AGENT_HOST', '127.0.0.1'),
        'statsd_port': 8125
    }
    initialize(**options)
    _statsd_enabled = True
else:
    _statsd_enabled = False

def emit_agent_step_metric(agent_name: str):
    """Emits a counter metric for each agent step."""
    if _statsd_enabled:
        statsd.increment('triagecrew.agent.step', tags=[f'agent:{agent_name}'])

def emit_final_decision_metric(decision: str, matched_rule: str):
    """Emits a counter metric for the final ticket decision."""
    if _statsd_enabled:
        statsd.increment(
            'triagecrew.ticket.processed',
            tags=[f'decision:{decision}', f'matched_rule:{matched_rule}']
        )
