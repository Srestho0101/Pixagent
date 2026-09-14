# Next Projects — Reuse the Patterns

Once you are comfortable with Pixagent, build one of these. Each reuses the same mental models while stretching a different muscle.

## 1. Internal Knowledge Bot (Tool + Light RAG)

- Source of truth: a small set of Markdown docs + a `documents` table.
- Tools: `search_docs(query)`, `get_document(id)`.
- Keep the same FastAPI + SSE + JWT skeleton.
- Goal: learn when to combine tool calling with simple keyword or embedding search.

## 2. Multi-Technician Shop with Roles

- Add a `role` column (`owner`, `tech`, `viewer`).
- Protect routes by role.
- Let owners re-assign tickets.
- Still keep the customer agent grounded only in the current ticket.

## 3. Parts Inventory Agent

- New tables: `parts`, `part_orders`.
- Tools: `check_stock(part_name)`, `get_eta(part_id)`.
- Technician can ask the agent “Do we have a keyboard for the X1?” while looking at a ticket.
- Practice multi-tool turns.

## 4. Customer Magic-Link Login

- Replace “know the ticket ID” with a short-lived signed link or OTP.
- Keep the agent exactly as it is.
- Learn token design and email/SMS integration.

## 5. Observability Layer

- Table `agent_runs` (ticket_id, messages, tool_calls, final_answer, latency, model).
- Simple admin page that shows recent runs and failure modes.
- Add a “thumbs up / down” button that stores feedback.
- This is the foundation of any serious agent product.

## 6. Multi-Provider Agent

- Abstract the LLM call behind a small interface (`OpenAICompatibleClient`).
- Support Mistral + one other provider (Groq, OpenAI, Anthropic, etc.).
- Keep the tool schema identical.
- Learn how thin the provider boundary can be.

## 7. Mini Multi-Agent System

- One “router” agent that decides whether to call the repair agent or a new “FAQ agent”.
- Still pure Python, no heavy framework.
- Goal: understand orchestration without drowning in abstractions.

---

Pick the one that feels most useful for *your* next real need. Ship a working version in a weekend. Then come back and update these learning notes with what you discovered.
