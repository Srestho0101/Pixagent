# Exercise 02 — Add a Second Tool

**Time**: 1–2 hours  
**Goal**: Extend the agent without breaking existing behaviour. This is the most transferable skill.

## The New Tool

Add `get_ticket_status`:

```json
{
  "name": "get_ticket_status",
  "description": "Get the current official status of the customer's ticket. Use when the user asks about overall progress or readiness for pickup.",
  "parameters": {
    "type": "object",
    "properties": {
      "ticket_id": {"type": "integer"}
    },
    "required": ["ticket_id"]
  }
}
```

## Requirements

1. The tool must still force the current customer’s `ticket_id`.
2. It should return a clean JSON object: `{"ticket_id": N, "status": "...", "device_info": "..."}`.
3. The system prompt should mention that the status tool exists and that the status in the context block is authoritative.
4. Existing edge-case prompts must still pass (especially the ones about not inventing completion).
5. Add 2–3 new prompts to `agent_edge_case_prompts.md` that specifically exercise the new tool.

## Implementation Hints

- Add the tool definition to the `TOOLS` list.
- Extend `_tool_result` with a new `if name == "get_ticket_status":` branch.
- You can reuse the connection already opened or open a fresh one — both are fine for this scale.
- Keep temperature low and max_tokens modest.

## Stretch Goals

- Support multi-tool responses (the model asks for both logs and status in one turn).
- Log every tool call to a simple `agent_tool_calls` table for later analysis.
- Make the tool also return the count of logs so the model can decide whether to fetch them.

## Success Criteria

- You can ask “What is the current status?” and the model either answers from context or correctly calls the new tool.
- Asking about another ticket ID still fails safely.
- The seeded battery-vs-keyboard scenario still distinguishes completed work from waiting parts.
