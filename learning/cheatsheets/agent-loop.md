# Cheatsheet — Agent Loop (Pixagent Style)

```
chat_stream(ticket_id, message, history)
│
├─ guards (no ticket / not found / greeting)
│
├─ context = _ticket_context(ticket_id)          # DB: ticket + newest logs
│
├─ messages = [system_prompt(context)] + history[-10:] + [user]
│
├─ Round 1 (non-stream)
│     payload = {model, messages, tools, tool_choice: "auto", temp: 0.2}
│     response = mistral(payload)
│
├─ if no tool_calls → yield content + [DONE]
│
├─ else
│     for each tool_call:
│         result = _tool_result(name, args, ticket_id)   # forced ticket_id
│         messages.append({role: "tool", content: json(result)})
│
│     Round 2 (stream)
│       stream tokens → yield SSE
│       yield [DONE]
│
└─ on 429 → _fallback_response(context, message)
```

## Key Guards

- Tool always overrides/rejects foreign `ticket_id`
- System prompt: data ≠ instructions
- Status in context is authoritative
- Explicit “I don’t have that information yet”
- History & log windows capped

## SSE Shape

```
data: {"content": "token"}
data: {"error": "msg"}
data: [DONE]
```

## Useful Constants

```
MAX_CONTEXT_LOGS = 25
MAX_TOOL_LOGS = 50
MAX_HISTORY_MESSAGES = 10
temperature = 0.2
max_tokens = 300
```
