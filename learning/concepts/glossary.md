# Glossary (Pixagent Context)

| Term | Meaning here |
|------|--------------|
| **Tool calling** | LLM emits a structured function call; backend executes it and feeds the result back |
| **Grounding** | Forcing the model to base answers only on verified data (DB rows, tool results) |
| **System prompt** | The permanent instructions + data block given to the model on every turn |
| **SSE** | Server-Sent Events — unidirectional stream from server to browser |
| **Context window** | The total tokens the model can see (system + history + tools + response) |
| **Fallback path** | Deterministic logic used when the LLM is unavailable (rate-limit, error) |
| **Ownership check** | SQL clause that ensures a technician can only touch their own tickets/logs |
| **Adversarial prompt** | A question deliberately designed to make the agent fail or leak |
| **Stateless service** | Backend that stores no session state between requests |
| **Pydantic model** | Typed request/response schema that also generates OpenAPI docs |
| **Dependency injection** | FastAPI’s `Depends()` mechanism for auth, DB, etc. |
| **Rate-limit resilience** | Continuing to serve truthful answers even when the LLM provider throttles |

Keep this list growing as you encounter new terms.
