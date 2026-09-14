# Exercise 01 — Break and Fix (Warm-up)

**Time**: 45–90 minutes  
**Goal**: Make the agent fail in controlled ways, then restore correctness. This builds the debugging muscle.

## Tasks

### 1. Force a cross-ticket leak (then seal it)

1. Create two tickets (or use the seed + another one).
2. Temporarily comment out or weaken the `requested_id != ticket_id` check in `_tool_result`.
3. In the chat for ticket A, ask something that might make the model call the tool with ticket B’s ID.
4. Observe the leak.
5. Restore the guard and confirm the leak is gone.
6. Write one new edge-case prompt that tries the same attack.

### 2. Make the model invent a cost

1. Ask “What was the final repair cost?” on the seeded ticket (the answer is not in the logs).
2. Confirm the model says it doesn’t know.
3. Temporarily soften the system prompt (remove the “never invent” / “I don’t have that information yet” language).
4. Ask again and watch it invent a number.
5. Restore the original wording.

### 3. Break streaming

1. In `_stream_final_response`, comment out the final `yield "data: [DONE]\n\n"`.
2. Observe how the frontend behaves (it will hang or never unlock the input).
3. Restore it.
4. Bonus: make the frontend show a timeout message if `[DONE]` never arrives within 30 s.

### 4. Ownership bypass (technician side)

1. Log in as technician A.
2. Note a ticket ID belonging to A.
3. Temporarily remove the `AND technician_id = %s` clause from one of the mutating routes (update or delete).
4. Confirm you can now affect another technician’s ticket (if you have one).
5. Put the clause back.

### 5. Rate-limit path

1. Temporarily raise an artificial `MistralRateLimitError` at the top of the first LLM call.
2. Confirm the fallback answer is still truthful and uses the verified context.
3. Remove the artificial raise.

## Debrief

Write 3–5 sentences answering:

- Which failure mode was easiest to introduce?
- Which one would have been hardest for a real user to notice?
- What single line of code now feels the most important?

Keep the answers in a private note or commit them as `learning/exercises/01-answers.md` (gitignored if you prefer).
