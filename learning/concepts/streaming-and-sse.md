# Streaming Responses & Server-Sent Events (SSE)

## Why Stream?

Users hate waiting 4–8 seconds for a complete LLM reply.  
Streaming tokens as they are generated creates the illusion of a fast, thinking assistant.

## How Pixagent Does It

### Backend

`app/routes/chat.py`:

```python
return StreamingResponse(
    chat_stream(...),                 # generator
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",    # important behind some proxies
    },
)
```

`chat_stream` yields strings that look like:

```
data: {"content": "The "}
data: {"content": "battery "}
data: {"content": "replacement "}
...
data: [DONE]
```

Or on error:

```
data: {"error": "The repair assistant is temporarily unavailable: ..."}
data: [DONE]
```

### Frontend (`frontend/app.js`)

The chat client uses `fetch` + `ReadableStream` (or equivalent) to read the body incrementally, parse each `data: ...` line, and append the `content` tokens to the UI in real time.

## SSE vs WebSockets vs Long Polling

| Method | Direction | Complexity | Good for |
|--------|-----------|------------|----------|
| SSE | Server → Client | Low | LLM token streaming, notifications |
| WebSocket | Bidirectional | Higher | Full duplex chat, games, collaborative editing |
| Long polling | Client → Server | Medium | Fallback when SSE is blocked |

For pure “LLM speaks to user” flows, SSE is usually the simplest correct choice.

## Important Implementation Details

1. **Two-phase call** (non-stream then stream)  
   Tool decisions need the complete JSON. Only the final natural-language answer is streamed.

2. **Always end with `[DONE]`**  
   The client needs a clear signal that the stream is finished.

3. **Error as a normal SSE event**  
   Don’t just close the connection; send `{"error": "..."}` so the UI can show a friendly message.

4. **Proxy buffering**  
   Some reverse proxies (nginx, etc.) buffer by default. The `X-Accel-Buffering: no` header (and proper proxy config) prevents that.

5. **Client must handle partial JSON / network blips**  
   Real networks drop. Robust clients reassemble or recover gracefully.

## How to Debug Streaming

1. Open browser DevTools → Network → the `/api/chat` request.
2. Confirm `Content-Type: text/event-stream`.
3. Look at the Response tab; you should see the `data:` lines appear one after another.
4. If everything arrives in one chunk, a proxy is buffering.

## Extending the Pattern

- Add a `ping` / heartbeat comment every 15 s for long-running streams.
- Support cancellation (AbortController on the client + checking a flag on the server).
- Switch to WebSockets later if you need bidirectional control (e.g. “stop generating”).

---

**Related code**: `app/agent.py` (`_sse`, `_stream_final_response`, `chat_stream`), `app/routes/chat.py`, frontend chat handling in `app.js`.
