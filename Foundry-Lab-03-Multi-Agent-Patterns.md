# Lab Guide 3 - Multi-Agent Patterns with Azure AI Foundry

## Workshop overview

This third lab extends the hosted-agent example from Lab Guide 2 into a practical multi-agent system.

Participants will evolve the **Contoso Field Service Assistant** into a set of specialist agents that communicate, delegate, review, and produce a governed final answer.

## Duration

**80 minutes**

## Scenario continuity

In Lab Guide 1, you built a prompt agent.

In Lab Guide 2, you built and productionized a hosted agent.

In this lab, you split that hosted agent into multiple cooperating agents:

- Router Agent
- Warranty Agent
- Troubleshooting Agent
- Escalation Agent
- Customer Communications Agent
- Reviewer Agent
- Supervisor Agent

## Workshop goal

Show when multi-agent design is useful, how agents communicate, and how to keep the system observable, safe, and cost-aware.

## Key message

Multi-agent systems are useful when specialization, review, parallelism, or governance matter. They are not automatically better than a single agent.

---

# Lab structure

| Section | Topic | Time |
|---|---|---:|
| 1 | From single agent to multi-agent | 8 min |
| 2 | Router and specialist agents | 15 min |
| 3 | Planner-executor workflow | 12 min |
| 4 | Agent-to-agent communication | 12 min |
| 5 | Reviewer and critic pattern | 12 min |
| 6 | Supervisor synthesis | 8 min |
| 7 | Multi-agent observability and cost | 10 min |
| 8 | Design checklist | 3 min |

---

# 1. From single agent to multi-agent

## Goal

Identify why the hosted agent from Lab Guide 2 should be decomposed.

## Baseline prompt

Run the original hosted agent with this request:

```text
Customer C-1042 reports recurring device failures after a firmware update.
Check warranty, classify severity, troubleshoot the issue, and draft next steps for the customer.
```

## Discussion

The single hosted agent must do many things:

- Understand the user request.
- Retrieve product and policy knowledge.
- Check warranty status.
- Classify severity.
- Draft an escalation.
- Write customer-safe communication.
- Avoid unsafe or unsupported actions.
- Explain confidence and missing information.

## Multi-agent decomposition

| Agent | Responsibility |
|---|---|
| Router Agent | Understand request and route work |
| Warranty Agent | Check warranty rules and contract/tool data |
| Troubleshooting Agent | Use product docs and known-issue guidance |
| Escalation Agent | Apply severity and escalation policy |
| Customer Communications Agent | Draft customer-safe response |
| Reviewer Agent | Check groundedness, policy compliance, safety, and tone |
| Supervisor Agent | Combine outputs into final response |

## Outcome

You understand the reason for the multi-agent split.

---

# 2. Router and specialist agents

## Goal

Build the first multi-agent pattern: a router delegating to specialist agents.

## Pattern

```text
User request
  -> Router Agent
  -> Warranty Agent
  -> Troubleshooting Agent
  -> Escalation Agent
  -> Supervisor Agent
  -> Final answer
```

## Router Agent instructions

```text
You are the Router Agent for Contoso Field Services.

Your job is to inspect the user request and decide which specialist agents should handle it.

Available agents:
- Warranty Agent: warranty coverage, replacement eligibility, customer/device entitlement.
- Troubleshooting Agent: product issues, firmware problems, field engineer steps.
- Escalation Agent: severity classification, escalation evidence, escalation drafting.
- Customer Communications Agent: customer-safe wording and response drafts.

Return a structured routing plan with:
- required_agents
- reason_for_each_agent
- missing_information
```

## Specialist inputs

Use a shared structured case object:

```json
{
  "customer_id": "C-1042",
  "device_id": "D-7781",
  "issue": "Recurring device failures after firmware update",
  "region": "West Europe",
  "business_impact": "Unknown",
  "requested_action": "Check warranty, classify severity, draft next steps"
}
```

## Test prompt

```text
Customer C-1042 reports that device D-7781 repeatedly fails after a firmware update.
Can we replace it, should this be escalated, and what should we tell the customer?
```

## Expected routing

The Router Agent should select:

- Warranty Agent.
- Troubleshooting Agent.
- Escalation Agent.
- Customer Communications Agent.

## Outcome

You have a router pattern that sends work to specialist agents.

---

# 3. Planner-executor workflow

## Goal

Show a multi-step plan where different agents execute different parts.

## Pattern

```text
Planner Agent
  -> Step 1: collect facts
  -> Step 2: check warranty
  -> Step 3: troubleshoot
  -> Step 4: classify escalation
  -> Step 5: draft response
  -> Step 6: review
```

## Planner Agent instructions

```text
You are the Planner Agent.

Break the case into clear execution steps.
Assign each step to the correct specialist agent.
Do not solve the case yourself.
Return a plan with ordered steps, assigned agent, required inputs, and expected output.
```

## Example plan output

```json
{
  "steps": [
    {
      "step": 1,
      "agent": "Warranty Agent",
      "task": "Check warranty status for customer C-1042 and device D-7781"
    },
    {
      "step": 2,
      "agent": "Troubleshooting Agent",
      "task": "Find firmware failure troubleshooting steps"
    },
    {
      "step": 3,
      "agent": "Escalation Agent",
      "task": "Classify severity and identify missing evidence"
    },
    {
      "step": 4,
      "agent": "Customer Communications Agent",
      "task": "Draft customer-safe next steps"
    },
    {
      "step": 5,
      "agent": "Reviewer Agent",
      "task": "Check the final response for grounding, safety, and policy compliance"
    }
  ]
}
```

## Outcome

You have a planner-executor workflow that makes agent responsibilities explicit.

---

# 4. Agent-to-agent communication

## Goal

Show how agents pass structured messages and intermediate outputs to each other.

## Communication principles

Agent messages should be:

- Structured.
- Minimal.
- Source-aware.
- Safe to pass downstream.
- Explicit about uncertainty.

## Shared message contract

```json
{
  "case_id": "CASE-9001",
  "agent_name": "Warranty Agent",
  "status": "completed",
  "findings": [],
  "sources": [],
  "tool_calls": [],
  "missing_information": [],
  "confidence": "medium"
}
```

## Warranty Agent output example

```json
{
  "case_id": "CASE-9001",
  "agent_name": "Warranty Agent",
  "status": "completed",
  "findings": [
    "Device D-7781 appears eligible for warranty review, but replacement approval requires failure code and installation date."
  ],
  "sources": [
    "warranty-rules.md"
  ],
  "tool_calls": [
    "lookup_warranty_status"
  ],
  "missing_information": [
    "Failure code",
    "Installation date"
  ],
  "confidence": "medium"
}
```

## Demo flow

1. Run the Router Agent.
2. Pass the case object to selected specialist agents.
3. Return each specialist output using the shared message contract.
4. Pass all specialist outputs to the Supervisor Agent.

## Outcome

Agents communicate through structured handoffs instead of unbounded chatty text.

---

# 5. Reviewer and critic pattern

## Goal

Add a Reviewer Agent that checks the proposed answer before the user sees it.

## Reviewer Agent instructions

```text
You are the Reviewer Agent.

Review the proposed final answer and specialist outputs.

Check:
- Is every policy claim grounded in a source?
- Did any agent invent warranty, safety, or escalation details?
- Are risky actions only drafted, not submitted?
- Is the customer response safe and professional?
- Are missing facts clearly stated?

Return:
- approved: true or false
- issues
- required_fixes
- final_recommendation
```

## Deliberate failure demo

Give the Supervisor Agent a flawed draft:

```text
Tell the customer this is definitely covered by warranty and that we have opened a Sev 1 escalation.
```

## Expected review

The Reviewer Agent should reject the draft because:

- Warranty is not confirmed.
- Sev 1 evidence is missing.
- Final business action should not be claimed if only a draft exists.

## Outcome

You have a critic/reviewer pattern that improves safety and quality before the final response.

---

# 6. Supervisor synthesis

## Goal

Combine specialist outputs into one final answer.

## Supervisor Agent instructions

```text
You are the Supervisor Agent.

Combine specialist agent outputs into a final answer for the user.

Rules:
- Prefer source-backed specialist findings.
- Preserve uncertainty and missing information.
- Do not overrule the Reviewer Agent.
- If the Reviewer Agent rejects the draft, revise it before responding.
- Keep the final answer concise, operational, and safe.
```

## Final answer shape

```text
Summary
Warranty position
Troubleshooting guidance
Escalation assessment
Customer communication draft
Missing information
Recommended next steps
```

## Outcome

The multi-agent system produces one governed final answer.

---

# 7. Multi-agent observability and cost

## Goal

Trace the full multi-agent workflow and discuss operational trade-offs.

## Inspect the trace

Look for:

- Which agents ran.
- Order of execution.
- Inputs and outputs per agent.
- Tool calls per agent.
- Retrieved documents.
- Reviewer decision.
- Total latency.
- Token usage per agent.
- Total cost.

## Operational questions

```text
Did every agent need to run?
Could some agents run in parallel?
Which agent used the most tokens?
Which agent caused most latency?
Was the review step worth the cost?
Could a smaller model handle routing or review?
```

## Cost optimization ideas

| Optimization | Example |
|---|---|
| Model routing | Use a smaller model for Router Agent |
| Parallelism | Run Warranty and Troubleshooting agents at the same time |
| Conditional execution | Only run Escalation Agent when escalation intent exists |
| Short contracts | Pass structured facts, not full conversation history |
| Caching | Cache stable policy lookups |
| Review sampling | Review all high-risk cases, sample low-risk cases |

## Outcome

You can explain and optimize a multi-agent run using traces and metrics.

---

# 8. Design checklist

## When to use multi-agent

Use multi-agent patterns when you need:

- Specialist reasoning.
- Independent tool permissions.
- Parallel work.
- Separation of duties.
- Review or critic behavior.
- Human-in-the-loop control.
- Better auditability for complex decisions.

## When not to use multi-agent

Avoid multi-agent complexity when:

- A single agent handles the task reliably.
- The flow is short and deterministic.
- Latency is critical.
- Token budget is tight.
- There is no clear separation of responsibility.

## Final checkpoint

You now have a multi-agent version of the hosted Contoso Field Service Assistant with:

- Router pattern.
- Specialist agents.
- Planner-executor workflow.
- Structured agent-to-agent communication.
- Reviewer/critic validation.
- Supervisor synthesis.
- Multi-agent tracing and cost analysis.

This completes the three-part progression:

1. **Fundamentals:** build the prompt agent.
2. **Enterprise:** build and operate the hosted agent.
3. **Multi-agent:** extend the hosted agent into cooperating specialist agents.
