# Pixagent Learning Path

> **Goal**: Turn this vibe-coded repair-shop agent into a permanent skill set.
> You will understand *why* every piece exists, master the underlying concepts,
> and leave able to design, debug, and scale similar systems (and better ones).

This is not a passive README. It is a **structured curriculum**.

## How to Use This Directory

| Folder | Purpose |
|--------|---------|
| `concepts/` | Deep, reusable ideas (tool calling, grounding, FastAPI patterns, SSE, auth, etc.) |
| `walkthroughs/` | Line-by-line / flow-by-flow tours of *this* codebase |
| `exercises/` | Hands-on drills that force you to modify, break, and fix the project |
| `cheatsheets/` | Quick-reference cards you can keep open while coding |
| `diagrams/` | Text/ASCII + Mermaid diagrams of architecture & data flow |
| `projects/` | Ideas for your next 3–5 projects that reuse these patterns |

**Recommended order** (do not skip):

1. Read `concepts/00-mental-models.md`
2. Read `diagrams/architecture.md`
3. Do `walkthroughs/01-request-lifecycle.md`
4. Deep-dive `concepts/tool-calling-agents.md` + `walkthroughs/02-agent-loop.md`
5. Complete the first three exercises in `exercises/`
6. Keep the cheatsheets open while you experiment
7. When comfortable, pick a project from `projects/` and ship it

## Learning Philosophy

- **Code is the textbook**. Every concept points back to exact files and lines in this repo.
- **Adversarial thinking**. Agents fail in creative ways; we practice attacking them.
- **Progressive disclosure**. Start simple (what happens when a customer asks a question), then expand to production concerns (pooling, observability, multi-tool loops).
- **Transferable skills**. Everything here maps to larger systems (customer support bots, internal tools, multi-agent workflows, etc.).

## Quick Start (Right Now)

```bash
# From repo root
cd learning
cat concepts/00-mental-models.md
```

Then open `app/agent.py` side-by-side and start peeling.

---

*Created for the author of Pixagent. Update these notes as you learn more — they are yours.*
