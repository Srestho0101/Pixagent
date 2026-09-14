# Walkthrough 01 — Full Request Lifecycle

Goal: follow one complete customer question from browser to database to LLM and back.

## Setup

1. Have the backend running (`uvicorn app.main:app --reload`).
2. Have the frontend open (or just use `curl` / httpie).
3. Know a valid ticket ID (run `python seed_agent_test_data.py` if needed).

## Step-by-step

### 1. Frontend prepares the payload

In `frontend/app.js` the chat form builds something like:

```json
{
  "ticket_id": 42,
  "message": "Has the battery been replaced?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hi! I can help with ticket #42..."}
  ]
}
```

History is capped (see Pydantic `max_length=10`).

### 2. Request hits FastAPI

`POST /api/chat` → `app/routes/chat.py`

```python
def chat(data: ChatRequest):
    history = [item.model_dump() for item in data.history]
    return StreamingResponse(
        chat_stream(data.ticket_id, data.message, history),
        media_type="text/event-stream",
        ...
    )
```

Pydantic has already validated types and lengths.

### 3. Agent entry point

`app/agent.py` → `chat_stream(ticket_id, user_message, history)`

Guard clauses first:

- No ticket_id → “Please enter a valid ticket ID…”
- Ticket not found → friendly 404-style message
- Simple greeting → deterministic reply (no LLM cost)

### 4. Context loading

`_ticket_context(ticket_id)`:

```sql
SELECT id, device_info, status FROM tickets WHERE id = %s
SELECT note, created_at FROM repair_logs
  WHERE ticket_id = %s
  ORDER BY created_at DESC, id DESC
  LIMIT 25
```

Logs are reversed so the prompt sees chronological order.  
`total_logs` and `logs_truncated` are computed so the model knows when to call the tool for older notes.

### 5. System prompt construction

`_system_prompt(context)` embeds the verified data inside a clearly delimited block:

```
<ticket_data>
Ticket ID: 42
Device and issue: Lenovo X1 Carbon, swollen battery...
Current status: waiting_parts
Repair timeline (chronological):
- 2025-...: Battery replaced and tested...
- 2025-...: Keyboard part ordered...
</ticket_data>
```

Plus the hard rules (never invent, status is authoritative, etc.).

### 6. First LLM call (non-streaming)

```python
initial_payload = {
    "model": settings.MISTRAL_MODEL,
    "messages": [system, ...history, user],
    "tools": TOOLS,
    "tool_choice": "auto",
    "temperature": 0.2,
    "max_tokens": 300,
}
```

Response is fully buffered so we can inspect `tool_calls`.

### 7. Tool execution (if any)

`_tool_result(...)`:

- Parses arguments
- **Rejects any ticket_id that is not the current one**
- Runs the SQL with limit/offset clamping
- Returns a clean JSON object

The result is appended as a `role: "tool"` message.

### 8. Final streaming call

Second request with `stream: True`.  
`_stream_final_response` reads the SSE lines from Mistral, re-packages them as our own SSE events, and yields them.

### 9. Frontend consumes the stream

Tokens appear one by one in the chat bubble.  
When `data: [DONE]` arrives, the UI unlocks the input again.

### 10. Rate-limit path

If Mistral returns 429, `MistralRateLimitError` is raised and the fallback (`_fallback_response`) answers from the *same* verified context. The user still gets a truthful reply.

---

**Your turn**:  
Add a few `print` or `logging` statements inside `chat_stream` and `_tool_result`. Ask a question that forces a tool call and watch the sequence in the terminal.
