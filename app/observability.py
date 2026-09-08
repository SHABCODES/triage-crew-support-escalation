import os
from datadog import initialize, statsd
import litellm


def init_langsmith_tracing():
    """Initializes LangSmith tracing if an API key is present.

    LiteLLM's built-in "langsmith" callback authenticates using the
    LANGSMITH_API_KEY / LANGSMITH_PROJECT env vars specifically — it does
    NOT read LANGCHAIN_API_KEY / LANGCHAIN_PROJECT, even though those are
    the older LangChain-native tracing vars and are easy to set by mistake.
    Setting LANGCHAIN_API_KEY alone means litellm's callback registers
    (so nothing errors) but silently fails to authenticate when it tries
    to actually send a trace — no exception, no trace, no clue why.

    To be robust to either naming convention, we fall back to the
    LANGCHAIN_* vars if the LANGSMITH_* ones aren't set, and always end up
    setting the LANGSMITH_* vars explicitly so litellm can actually see them.
    """
    api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        return

    os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_PROJECT"] = (
        os.environ.get("LANGSMITH_PROJECT")
        or os.environ.get("LANGCHAIN_PROJECT")
        or "triagecrew"
    )

    litellm.success_callback = ["langsmith"]
    litellm.failure_callback = ["langsmith"]
    print(f"LangSmith tracing initialized via LiteLLM (project={os.environ['LANGSMITH_PROJECT']}).")

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
