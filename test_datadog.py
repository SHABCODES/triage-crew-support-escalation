import os
from datadog import initialize, statsd

print("Loading Datadog Config...")
options = {
    'statsd_host': os.environ.get('DD_AGENT_HOST', '127.0.0.1'),
    'statsd_port': 8125
}
initialize(**options)

print(f"Emitting manual test metric to {options['statsd_host']}...")
statsd.increment(
    'triagecrew.ticket.processed',
    tags=['decision:refund', 'matched_rule:BillingIssue']
)
statsd.increment('triagecrew.agent.step', tags=['agent:TestAgent'])

print("Metrics emitted! Check your Datadog Metrics Explorer.")
