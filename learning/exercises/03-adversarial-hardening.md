# Exercise 03 — Adversarial Hardening

**Time**: 1–2 hours  
**Goal**: Treat the agent like a security researcher would.

## Setup

```bash
python seed_agent_test_data.py --reset
# note the printed ticket ID
```

## Tasks

1. Run **every** prompt in `agent_edge_case_prompts.md` against a fresh chat session.
2. Record any failure (model invents data, leaks information, ignores status, etc.).
3. For each failure:
   - Identify which layer should have stopped it (prompt / tool guard / fallback).
   - Make the smallest change that fixes it.
   - Re-run the failing prompt and the neighbouring prompts to check for regressions.
4. Invent three *new* attack prompts that are not in the list and add them to the file.
5. (Optional) Add a simple automated test script that fires the prompts via the API and checks that the answer contains “I don’t have” or similar refusal language for the unknown questions.

## Success Criteria

- All original prompts behave correctly.
- Your three new attacks are also blocked.
- You can explain, for each major defense, what would happen if it were removed.

This exercise is the difference between a cool demo and something you would actually put in front of real customers.
