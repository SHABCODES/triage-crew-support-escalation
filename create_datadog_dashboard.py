import os
import sys
from datadog import initialize, api

def main():
    # Load keys from environment
    api_key = os.environ.get("DD_API_KEY")
    app_key = os.environ.get("DD_APP_KEY")
    
    if not api_key or not app_key:
        print("Error: DD_API_KEY and DD_APP_KEY environment variables are required.")
        print("Please generate an Application Key in Datadog (Organization Settings -> Application Keys).")
        sys.exit(1)

    options = {
        'api_key': api_key,
        'app_key': app_key,
        'api_host': 'https://api.datadoghq.com'
    }
    
    initialize(**options)

    print("Creating Datadog Dashboard...")
    dashboard_title = "TriageCrew Support Metrics"
    widgets = [
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "sum:triagecrew.ticket.processed{*} by {decision}.as_count()",
                        "display_type": "line",
                        "style": {
                            "palette": "dog_classic",
                            "line_type": "solid",
                            "line_width": "normal"
                        }
                    }
                ],
                "title": "Tickets Processed by Decision"
            }
        },
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "sum:triagecrew.agent.step{*} by {agent}.as_count()",
                        "display_type": "line",
                    }
                ],
                "title": "Agent Steps Executed"
            }
        }
    ]
    layout_type = "ordered"
    
    try:
        dash_response = api.Dashboard.create(
            title=dashboard_title,
            widgets=widgets,
            layout_type=layout_type,
            description="Dashboard for monitoring TriageCrew agent activity and ticket resolutions."
        )
        if 'id' in dash_response:
            print(f"Success! Dashboard created at: https://app.datadoghq.com/dashboard/{dash_response['id']}")
        else:
            print("Failed to create dashboard:", dash_response)
    except Exception as e:
        print("Error creating dashboard:", e)

    print("\nCreating Escalation Alert Monitor...")
    monitor_name = "TriageCrew High Escalation Rate"
    monitor_query = "sum(last_10m):sum:triagecrew.ticket.processed{decision:escalated}.as_count() > 5"
    monitor_message = (
        "{{#is_alert}}\n"
        "High volume of support tickets are being escalated!\n"
        "Check the TriageCrew dashboard to investigate.\n"
        "{{/is_alert}}"
    )
    monitor_tags = ["service:triagecrew", "env:production"]
    
    try:
        monitor_response = api.Monitor.create(
            type="metric alert",
            query=monitor_query,
            name=monitor_name,
            message=monitor_message,
            tags=monitor_tags,
            options={
                "thresholds": {"critical": 5.0, "warning": 3.0},
                "notify_audit": False,
                "require_full_window": True,
                "notify_no_data": False,
                "renotify_interval": 0
            }
        )
        if 'id' in monitor_response:
            print(f"Success! Monitor created with ID: {monitor_response['id']}")
        else:
            print("Failed to create monitor:", monitor_response)
    except Exception as e:
        print("Error creating monitor:", e)

if __name__ == "__main__":
    main()
