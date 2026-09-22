# Section 1 Lab Guide - Foundry Fundamentals

**Duration:** 80 minutes  
**Scenario:** Contoso Field Services

## Workshop objective

Build a useful prompt agent end to end, then explain how the same building blocks lead to hosted and multi-agent architectures.

## Prerequisites

- Access to the Azure AI Foundry portal.
- A Foundry project for Contoso Field Services.
- A deployed chat model.
- The Contoso support documents and prepared demo resources.
- The `DefaultAzureCredential` development environment if the code example is shown.

## Lab flow

| Chapter | Topic | Time |
|---|---|---:|
| 1 | Foundry Fundamentals | 5 min |
| 2 | Models and deployments | 7 min |
| 3 | Services | 5 min |
| 4 | Agents | 18 min |
| 5 | Tools, MCP and toolbox | 12 min |
| 6 | Memory | 8 min |
| 7 | Knowledge | 13 min |
| 8 | Recap and hand-off | 12 min |

---

# 1. Foundry Fundamentals

### Goal

Understand the Foundry resource and project hierarchy, and locate the Build and Operate areas.

### Walkthrough

1. Open the Foundry overview and identify the resource and project.
2. Point out the Build services: models, agents, tools, knowledge, memory, guardrails and data.
3. Point out the Operate services: evaluations, tracing and monitoring.
4. Open the use cases gallery and show the Media / Agents toggle and modality filters.
5. Open Text Chat with GPT-5.5 and ask one Contoso question.

### Discussion

This first answer is the destination experience. The rest of Section 1 takes it apart and rebuilds it from models, agents, capabilities, memory and knowledge.

---

# 2. Models and deployments

### Goal

Understand model selection as a quality, latency and cost decision.

### Walkthrough

1. Open the model catalog and filter by task and provider.
2. Open one model card and discuss its intended use.
3. Open the deployments list and inspect the deployed GPT-5.5 model.
4. Review version, region, TPM/quota and content-filter binding.
5. In Text Chat, send the same prompt to two deployments side by side.
6. In Reasoning Arena, compare the same multi-step prompt across reasoning deployments.
7. Point out latency and application-recorded token usage.
8. Show the project endpoint and the `DefaultAzureCredential` authentication pattern.

### Checkpoint

Choose a deployment for the Contoso agent and explain the trade-off behind the choice.

---

# 3. Services

### Goal

Build a mental map of the Foundry services and how they fit together.

### Walkthrough

1. Use the portal left navigation to locate models, agents, services, tools, knowledge, memory, guardrails and data.
2. Explain the Build versus Operate split.
3. Return to the use cases gallery and show how the same platform supports different experiences.

### Checkpoint

Explain which service supplies the model, which service supplies capabilities, and which services help operate the result.

---

# 4. Agents

### Goal

Create and refine a prompt agent, then explain how it differs from a hosted agent.

### Walkthrough

1. Open the pre-created Contoso Field Services agent.
2. Read the Instructions pane and explain that the instructions are the agent's main program.
3. Run a Contoso request in the Playground.
4. Open the Versions list and switch from v1 to v2.
5. Rerun the same prompt and identify the effect of the instruction change.
6. Show the Responses API call shape.
7. Compare prompt and hosted agents across runtime ownership, identity, scaling, endpoints, operations and cost.
8. Show the architecture and ownership diagrams.
9. Point to the existing hosted deployment without opening it.
10. Rerun the request and ask where it is executing.

### Checkpoint

Know when a prompt agent is sufficient and when the application needs a hosted runtime.

---

# 5. Tools, MCP and toolbox

### Goal

Add capabilities without hard-coding every branch into the application.

### Walkthrough

1. Open the agent Tools tab and review the attached tools.
2. Use Web Search for a time-sensitive question and expand the model-selected tool call.
3. Use File Search against an uploaded Contoso file.
4. Show the Custom Function schema and explain that implementation code remains outside the prompt.
5. Ask a Microsoft Learn question and inspect the MCP invocation and result.
6. Open the Toolbox and attach the same tool set to a second agent without rewiring.

### Checkpoint

Explain that the model selects a capability based on the request, while the tool contract controls what the capability can do.

---

# 6. Memory

### Goal

Distinguish conversation continuity and safe preference memory from tools and enterprise knowledge.

### Walkthrough

1. Open Memory and start a new thread.
2. State a safe response preference.
3. Ask a follow-up question that should reflect the preference.
4. Show the recall across the conversation.
5. Explain what must not be stored: secrets, personal data, confidential customer details or system-of-record data.

### Time-saving option

If the session is running late, mention Toolbox reuse on a slide rather than demonstrating it again.

---

# 7. Knowledge

### Goal

Ground answers in Contoso content and introduce Foundry IQ.

### Walkthrough

1. Show the chain: source -> chunk -> index -> knowledge source -> knowledge base -> MCP tool -> cited answer.
2. Open the Contoso knowledge source.
3. Open the Azure AI Search index and show fields and sample chunks.
4. Open the knowledge base and show the MCP tool it exposes.
5. Ask the grounded agent a question that requires a citation.
6. Follow the citation back to the source chunk.
7. Show Document Q&A as a build-it-yourself version using Azure AI Search.
8. Contrast Foundry IQ knowledge with the lightweight File Search capability.

### Checkpoint

Explain why deliberate indexing, knowledge sources and citations are different from simply putting documents into a prompt.

---

# 8. Recap and hand-off

### Goal

Connect the building blocks and prepare for enterprise operation.

### Walkthrough

1. Show the completed agent in one diagram: model, tools, memory and grounded knowledge.
2. Review what the agent can now do.
3. Open the Operate section once and point to evaluations, tracing and guardrails.
4. Close with the questions for Section 2: can the agent be observed, evaluated, protected and released safely?
5. Leave time for questions.

## Completion checkpoint

You have a working prompt agent and understand the path from a small agent to a hosted or multi-agent architecture.
