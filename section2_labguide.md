# Section 2 Lab Guide - End-to-End Enterprise AI

**Duration:** 80 minutes  
**Scenario:** Continue with the Contoso Field Services agent from Section 1.

## Workshop objective

Turn the Section 1 agent into a governed, observable and releasable service.

## Prerequisites

- A completed or pre-created Section 1 Contoso agent.
- A hosted Contoso agent deployment and prepared endpoint.
- Prepared traces, evaluation runs, guardrail prompts and release versions.
- Access to Foundry Traces, Insights, Monitor, Evaluation, Optimize and agent version views.
- Application Insights connected for the demonstration.

## Lab flow

| Chapter | Topic | Time |
|---|---|---:|
| 1 | Recap: build to operate | 5 min |
| 2 | Observability | 20 min |
| 3 | Evaluation & Optimization | 20 min |
| 4 | Guardrails | 20 min |
| 5 | Operate | 15 min |

---

# 1. Recap: build to operate

### Goal

Frame the operational questions for the session.

### Walkthrough

1. Show the Section 1 architecture beside the hosted, operated architecture.
2. Identify the four questions:
   - Can we observe the agent?
   - Can we evaluate and improve it?
   - Can we protect it?
   - Can we release it safely?
3. Acknowledge identity, permissions, Auth and OBO as cross-cutting foundations.

### Outcome

The audience understands why a useful agent needs more than a good prompt before it can serve real users.

---

# 2. Observability

### Goal

Use Foundry traces, Insights, Monitor and Application Insights to understand what happened during a request.

### Walkthrough

1. Open the trace from the guardrail prompt run earlier.
2. Expand the span tree and identify the model call, tool call and retrieval operation.
3. Compare latency across spans and identify the expensive operation.
4. Inspect token counts for each call.
5. Open Application Insights and find the same request as an end-to-end transaction.
6. Open the deployment quota and usage view and connect usage to cost.
7. Show the prompt/response capture setting.
8. Explain the privacy trade-off between richer diagnostics and sensitive telemetry.

### Investigation questions

- Which operation caused the latency?
- Which tool or retrieval result influenced the answer?
- How many tokens did the request consume?
- What information is captured in traces?
- What should be redacted or excluded?

### Outcome

You can trace a request across the agent and explain its latency, failures, token usage and privacy implications.

---

# 3. Evaluation & Optimization

### Goal

Use the Foundry Evaluation and Optimize experiences to assess and improve the agent.

### Walkthrough

1. Open the evaluation datasets.
2. Show the golden set and safety set, including a few rows.
3. Open the completed baseline run and review the evaluators and scores.
4. Open the completed second run using changed instructions.
5. Open the comparison view and identify the score delta.
6. Drill into two or three failed rows and read one aloud.
7. Open Optimize and show how evaluation evidence informs improvement.
8. Explain the decision threshold: improve, promote or block.

### Important distinction

Evaluation measures behavior against prepared cases. Observability explains an individual runtime request. Guardrails enforce controls during execution. They support one another but are not interchangeable.

### Outcome

You can use Foundry UI evaluations and Optimize to identify regressions and decide whether a change is ready for release.

---

# 4. Guardrails

### Goal

Demonstrate how different guardrails shape the agent's behavior.

### Guardrail layers

1. Application checks.
2. Content Safety preflight.
3. Hosted-agent RAI policy.
4. Agent instructions and human review for consequential actions.

Treat user input, retrieved content and tool output as data, not instructions.

### Walkthrough

1. Open the deployment content filter / RAI policy.
2. Show categories and severity thresholds.
3. Open the prepared guardrail test panel.
4. Paste the injection prompt; do not type it live.
5. Observe the blocked or resisted result and name the layer that caught it.
6. Paste the unsupported Sev 1 escalation prompt.
7. Observe the needs-review result and identify the missing evidence or approval.
8. Paste the invented policy prompt.
9. Observe the refusal with no unsupported citation.
10. After each prompt, explain which guardrail produced the behavior.

### Expected examples

| Prompt type | Expected outcome |
|---|---|
| Injection attempt | Blocked or resisted |
| Unsupported Sev 1 escalation | Needs review |
| Invented policy | Refused; no citation offered |

### Outcome

You can explain that guardrails are layered controls, not a single instruction or filter.

---

# 5. Operate

### Goal

Manage releases safely using immutable versions and controlled promotion.

### Walkthrough

1. Open the agent versions list and show that versions are immutable.
2. Open the prepared draft and smoke-test it in the Playground.
3. Explain how evaluation results authorize or block promotion.
4. Promote the prepared green version while keeping blue available.
5. Open endpoint or traffic configuration and show traffic pointing to green.
6. Roll back to blue live.
7. Roll forward to green again.
8. Briefly connect release management to quotas, cost attribution, ownership and the broader Agent 365 operate context.

### Release principles

- Test drafts before promotion.
- Promote only versions that meet evaluation thresholds.
- Keep a known-good version available for rollback.
- Separate configuration by environment.
- Make ownership and operational responsibility explicit.

### Outcome

You can explain and demonstrate a safe release, rollback and promotion cycle for a governed agent.

## Completion checkpoint

The Section 1 prompt agent has now been connected to an enterprise operating model: observable requests, measurable quality, layered guardrails and controlled immutable releases.
