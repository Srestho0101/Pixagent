# Walkthrough 03 — Frontend Chat & Session

Focus: `frontend/app.js` (the chat-related parts).

## Session Model

- Technician JWT → `localStorage` (survives browser restart).
- Customer ticket ID → `sessionStorage` (cleared when the tab closes, and also cleared when the user looks up a different ticket).

When the ticket ID changes, the chat history is reset. This prevents the model from mixing context across tickets.

## Key Functions to Trace

1. `getSessionTicketId` / `saveSessionTicketId` / `clearSessionTicketId`
2. `resetChatConversation` — empties the message list and history array
3. `updateChatContext` — updates the small status line in the chat widget
4. The form submit handler that builds the payload and starts the stream
5. The stream consumer that appends tokens and handles `[DONE]` / error events

## Streaming Client Pattern (conceptual)

```js
const response = await fetch(`${API_BASE_URL}/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json", ... },
  body: JSON.stringify({ ticket_id, message, history }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
// loop: read chunks → split on \n\n → parse "data: ..." → append content
```

(Actual implementation details may vary slightly; read the real code.)

## UI State Machines

- Chat widget open / closed
- Input disabled while a stream is in progress
- Loading / error / success messages on forms
- Theme (light / dark) persisted in `localStorage`

## What to Experiment With

- Change the ticket mid-conversation and confirm history is wiped.
- Open two tabs, log in as the same technician, and watch localStorage stay in sync.
- Force a network error during a stream and observe the UI recovery path.
- Add a “Stop generating” button that aborts the fetch (AbortController).

After this walkthrough the frontend should feel as transparent as the backend agent loop.
