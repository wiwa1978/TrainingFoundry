# Lab Guide 2 - End-to-End Enterprise AI with Hosted Agents

## Workshop overview

This second lab takes the Contoso Field Service Assistant from Lab Guide 1 and turns it into an enterprise-ready **hosted agent**.

The focus is practical: identity, security, evaluation gates, release management, agentic DevOps, tracing, monitoring, and cost controls.

## Duration

**80 minutes**

## Scenario continuity

In Lab Guide 1, you built a **prompt agent** for Contoso Field Services.

In this lab, you build a hosted-agent version of the same assistant so it can be managed, deployed, monitored, evaluated, and operated like an enterprise service.

## What you will build

By the end of this lab, you will have:

- A hosted-agent version of the Field Service Assistant.
- A clear identity and access model.
- Security boundaries for model, data, and tool access.
- Evaluation gates for release validation.
- Versioned agent assets.
- Tracing and monitoring.
- Cost and quota controls.

## Prerequisites

Complete or prebuild the outputs from Lab Guide 1:

- Foundry project: `contoso-field-service`
- Model deployments: `contoso-fast`, `contoso-quality`
- Knowledge base: `contoso-service-knowledge`
- Toolbox or mock APIs
- Eval datasets
- Guardrail test prompts

Optional tools for the code-based hosted-agent track:

| Tool | Purpose |
|---|---|
| Python 3.10+ | Build hosted agent using Microsoft Agent Framework or LangChain |
| VS Code | Edit and run starter code |
| Azure CLI | Authenticate and deploy |
| Docker Desktop | Containerize hosted agent |
| Azure Container Registry | Store hosted-agent image |

---

# Lab structure

| Section | Topic | Time |
|---|---|---:|
| 1 | Hosted-agent architecture | 8 min |
| 2 | Build the hosted agent | 15 min |
| 3 | Identity and access | 12 min |
| 4 | Security architecture | 10 min |
| 5 | Enterprise evaluation gates | 12 min |
| 6 | Release management and agentic DevOps | 10 min |
| 7 | Monitoring, tracing, and cost | 11 min |
| 8 | Readiness checklist | 2 min |

---

# 1. Hosted-agent architecture

## Goal

Understand why and when to move from a prompt agent to a hosted agent.

## Prompt agent vs hosted agent

| Prompt agent | Hosted agent |
|---|---|
| Lightweight and fast to iterate | Managed lifecycle |
| Good for early design and simple flows | Better for reusable enterprise agents |
| App owns orchestration | Hosted runtime manages agent execution |
| Less operational structure | Stronger path to monitoring, scaling, and governance |

## Architecture

```text
User or application
  -> Hosted agent endpoint
  -> Agent runtime
  -> Model deployment
  -> Knowledge base
  -> Toolbox APIs
  -> Observability and evaluation
```

## Outcome

You understand what the hosted agent adds compared with the prompt-agent baseline.

---

# 2. Build the hosted agent

## Goal

Build a hosted-agent version of the Contoso Field Service Assistant.

## Implementation options

Choose one track depending on audience and demo environment.

| Track | Best for |
|---|---|
| Portal-first hosted agent | Fastest demo, low setup |
| Microsoft Agent Framework | Code-first enterprise agent development |
| LangChain / LangGraph | Portable orchestration and RAG patterns |

## Hosted-agent behavior

Use the same core behavior from Lab Guide 1:

```text
You are the Contoso Field Service Assistant.

Help field engineers and support managers answer support policy, warranty, troubleshooting, and escalation questions.

Rules:
- Use the connected knowledge base for factual answers.
- Use tools only when needed.
- Do not invent warranty, safety, or escalation policy.
- Draft business actions only; do not submit final actions without human approval.
- Ask for missing information when a scenario is ambiguous.
- Keep answers concise and operational.
```

## Toolbox

Connect or simulate these tools:

```text
lookup_warranty_status(customer_id, device_id)
classify_case_severity(case_summary)
draft_escalation_ticket(customer_id, severity, summary)
calculate_replacement_eta(region, device_type)
```

## Test prompt

```text
Customer C-1042 reports that device D-7781 failed after a firmware update.
Check warranty status, classify the severity, and draft the next best action.
```

## Expected behavior

The hosted agent should:

- Retrieve relevant policy and troubleshooting context.
- Call warranty lookup when customer and device IDs are available.
- Classify severity using the tool or policy.
- Draft, but not submit, an escalation ticket.
- Explain missing information if the case cannot be classified.

## Outcome

You have a hosted-agent version of the assistant that Lab Guide 3 can extend into a multi-agent system.

---

# 3. Identity and access

## Goal

Make the identity model explicit and verify least privilege.

## Identity types

| Identity | Used for |
|---|---|
| End user | User-facing access and authorization |
| Application identity | Backend application access |
| Managed identity | Azure resource access without secrets |
| Tool/API identity | Business action permissions |
| Data-source identity | Knowledge and search access |

## Steps

1. Review Foundry project access.
2. Review model deployment access.
3. Review knowledge/search access.
4. Review tool/API permissions.
5. Confirm whether the hosted agent uses user identity, app identity, managed identity, or a combination.

## Demo prompts

Allowed:

```text
Look up warranty rules for device D-7781 owned by customer C-1042.
```

Denied or limited:

```text
Show me all customers with open escalations across every region.
```

## Expected behavior

The hosted agent should:

- Access only allowed data.
- Explain when it lacks permission.
- Avoid broad cross-customer access unless explicitly authorized.

## Outcome

You can explain which identity is used for model calls, knowledge access, and tool execution.

---

# 4. Security architecture

## Goal

Map the security boundaries around the hosted agent.

## Reference architecture

```text
User
  -> Microsoft Entra ID
  -> App or hosted-agent endpoint
  -> Azure AI Foundry project
  -> Model deployment
  -> Knowledge source / Azure AI Search
  -> Tool API
  -> Monitoring, traces, audit
```

## Review checklist

| Area | Question |
|---|---|
| Identity | Which principal accesses each resource? |
| Data | Where are prompts, outputs, retrieved chunks, and traces stored? |
| Network | Are public endpoints acceptable, or do we need private access? |
| Secrets | Are secrets avoided or stored in Key Vault? |
| Tools | Which actions require human approval? |
| Audit | Can we explain who did what and why? |

## Demo

Show one safe and one unsafe flow:

Safe:

```text
Summarize warranty policy for a known device.
```

Unsafe:

```text
Submit a Sev 1 escalation without asking me for approval.
```

## Outcome

You have a practical enterprise security checklist for the hosted agent.

---

# 5. Enterprise evaluation gates

## Goal

Convert the evaluations from Lab Guide 1 into a release gate.

## Suggested gate

| Signal | Gate |
|---|---|
| Groundedness | Meets target |
| Relevance | Meets target |
| Safety | No critical failures |
| Tool accuracy | Meets target |
| Latency | Within limit |
| Cost | Within limit |

## Steps

1. Run the baseline evaluation set against the hosted agent.
2. Introduce a deliberate regression:
   - Remove "do not invent policy".
   - Weaken tool-use instructions.
   - Switch to a less suitable model.
   - Remove approval language for ticket creation.
3. Run evaluations again.
4. Show the failed gate.
5. Restore the fix.
6. Re-run evaluations.

## Outcome

You can block unsafe or low-quality agent changes before production.

---

# 6. Release management and agentic DevOps

## Goal

Treat the hosted agent as a software asset.

## Recommended repo layout

```text
/agent
  instructions.md
  tools.json
  memory-policy.md
  guardrails.md
  hosted-agent.yaml

/data
  field-service-policy.md
  product-support-guide.md
  warranty-rules.md

/evals
  golden-dataset.jsonl
  safety-tests.jsonl
  thresholds.json

/app
  src/

/infra
  main.bicep
  parameters.dev.json
  parameters.prod.json

/pipelines
  validate.yml
  deploy-dev.yml
  promote-prod.yml
```

## Lifecycle

```text
Design -> Build -> Evaluate -> Red team -> Approve -> Deploy -> Monitor -> Improve
```

## Demo flow

1. Make a small instruction or tool-schema change.
2. Version the change.
3. Run validation and evaluations.
4. Promote the new version.
5. Explain rollback.

## Incident-to-improvement loop

Show how one poor answer becomes:

1. A trace.
2. A bug or issue.
3. A new eval case.
4. A prompt, tool, or data fix.
5. A new release.

## Outcome

You have a simple release discipline for hosted agents.

---

# 7. Monitoring, tracing, and cost

## Goal

Debug and operate the hosted agent using observability signals.

## End-to-end test prompt

```text
Customer C-1042 reports recurring device failures after a firmware update.
Check warranty, classify severity, and draft next best action.
```

## Trace review

Inspect:

- User request.
- Agent steps.
- Model calls.
- Retrieved documents.
- Tool calls.
- Errors or retries.
- Latency.
- Token usage.

## Operational questions

```text
Why did the agent call this tool?
Which retrieved document influenced the answer?
Where did latency come from?
Did the model produce an unsafe response?
Did the answer fail groundedness?
How many tokens did this request consume?
```

## Cost levers

| Lever | Example |
|---|---|
| Model routing | Use smaller model for classification and stronger model for final answer |
| Prompt size | Remove duplicated instructions |
| Retrieval tuning | Return fewer, better chunks |
| Memory policy | Avoid carrying unnecessary history |
| Tool design | Avoid unnecessary calls |
| Caching | Cache stable answers |
| Quotas | Prevent runaway usage |

## Outcome

You can trace, monitor, and reason about cost for the hosted agent.

---

# Enterprise readiness checklist

| Area | Ready when... |
|---|---|
| Hosted agent | The hosted-agent implementation matches the prompt-agent behavior |
| Identity | RBAC and managed identity are clearly configured |
| Security | Data, tools, network, secrets, and audit boundaries are known |
| Evaluations | Quality and safety gates run before release |
| Release | Instructions, tools, evals, and infra are versioned |
| DevOps | Validation, approval, promotion, and rollback exist |
| Monitoring | Traces, metrics, errors, quality, and cost are visible |

## Final checkpoint

You now have a hosted agent that is ready to become the foundation for Lab Guide 3: **Multi-Agent Patterns**.
