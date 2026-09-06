# Operations & Observability Runbook

## 1. Create three free accounts
LangSmith (smith.langchain.com), Datadog (datadoghq.com), and Rootly (rootly.com, plus connect it to a free personal Slack workspace). No credit card needed for any of them. Grab the LangSmith and Datadog API keys now — you'll paste them into `.env` in the next step. Rootly's setup can wait until step 5.

## 2. Run the project locally with tracing on
Unzip the patched repo, run `cp .env.example .env`, fill in `OPENAI_API_KEY`, `API_KEY`, `LANGSMITH_API_KEY`, and `DD_API_KEY`, then `docker-compose up --build`. Send a few `POST /tickets` requests using the example in the README. Confirm traces are showing up in your LangSmith project and APM traces are showing up under Datadog > APM > Services > triagecrew.

## 3. Build one Datadog dashboard and one alert
In Datadog, add a timeseries widget on the custom metric `triagecrew.ticket.processed`, grouped by `decision`, so you can see auto-resolve vs. escalate rate. Then create a monitor that alerts if escalations spike over a short window — this is the signal that triggers the incident in step 5.

## 4. Deploy to Kubernetes with minikube
Install minikube locally, run `minikube start`, then `eval $(minikube docker-env)` and `docker build -t triagecrew:local .` so the image is visible inside minikube. Copy `k8s/secret.example.yaml` to `k8s/secret.yaml` with real values, then `kubectl apply` the configmap, secret, deployment, and service. Confirm the pod is Running with `kubectl get pods`, and hit it with `minikube service triagecrew --url` plus a real `POST /tickets` request.

## 5. Simulate one incident through Rootly
Send a burst of tickets worded to trigger repeated escalations (billing-related or containing flagged keywords) until your Datadog alert fires. Open an incident in Rootly from Slack, assign yourself as incident commander, and use the LangSmith trace plus Datadog APM trace for one escalated ticket to find the specific agent step and guardrail rule responsible.

## 6. Resolve it and write the postmortem
Close the incident in Rootly and let it draft the postmortem, then fill it in with what you actually found: what happened, how it was detected, the root cause (name the specific `matched_rule`), and one concrete follow-up action. Save the exported doc in the repo under `postmortems/`. This file is the artifact that makes the whole exercise verifiable.

## 7. Turn it into a story you can tell
The resume line is one sentence, but the interview version is the sequence: a burst of billing tickets pushed the escalation rate up → a Datadog alert caught it → you opened a Rootly incident → traced the exact agent step in LangSmith → identified the guardrail rule causing it → wrote a postmortem with a concrete fix. That sequence, told in that order, is what 'proven experience supporting AI platforms' actually sounds like when it's true.
