# 00 — Mental Models for Building Agent Systems

These are the high-level lenses you should keep in your head forever.

## 1. Agent = LLM + Tools + Memory + Orchestration

Most “AI agent” frameworks are just convenience layers around this loop:

```
while not done:
    response = llm(messages, tools)
    if response has tool_calls:
        results = execute_tools(tool_calls)
        messages.append(tool_results)
    else:
        return response.content
```

Pixagent implements a **minimal, production-shaped version** of this loop in pure Python (`app/agent.py`).  
Once you can read and modify that file confidently, you understand 80 % of every agent library.

## 2. Grounding Beats Prompting

When the source of truth is structured (tickets, inventory, orders, user records):

- Prefer **tool calling** + verified context over pure RAG.
- Prefer **“I don’t know”** over a confident hallucination.
- Treat the system prompt as *code*, not poetry. Version it. Attack it.

Pixagent’s system prompt + tool guard is a textbook example of grounding.

## 3. Defense in Depth for Agents

Three layers that must all fail for a bad answer to escape:

1. **Prompt rules** (“never invent”, “only use ticket data”)
2. **Tool implementation** (force `ticket_id` to the customer’s ticket)
3. **Fallback / rate-limit path** (deterministic answer from the same context)

Never rely on the LLM alone.

## 4. Stateless Services + Client State

The FastAPI backend is almost completely stateless.  
Conversation history and current ticket live in the browser (`sessionStorage` / `localStorage`).

Benefits:
- Easy horizontal scaling
- Simple restart / deploy
- Clear ownership of data

Trade-off: you must re-fetch context on every turn (which Pixagent already does).

## 5. Thin Controllers, Fat Domain Logic

- Routes (`app/routes/*`) only validate, authorize, and call the next layer.
- Domain logic lives in `agent.py`, `auth.py`, or future service modules.
- Pydantic models own validation and OpenAPI docs.

This pattern scales to very large codebases.

## 6. Start With the Data Model

The three tables (`technicians`, `tickets`, `repair_logs`) + the status enum dictate almost everything else:

- API shape
- What the agent is allowed to say
- What the UI must display
- What needs indexes

Always design the schema (and the adversarial test cases) before the pretty chat UI.

## 7. Adversarial Testing Is Part of the Product

`agent_edge_case_prompts.md` + `seed_agent_test_data.py` are not “nice to have”.  
They are the difference between a demo and something you can put in front of real customers.

Build the attack list *before* you trust the agent.

---

**Exercise for yourself**: After reading this file, close it and explain the seven models out loud (or write them in your own words). If any feel fuzzy, re-read the corresponding walkthrough later.
