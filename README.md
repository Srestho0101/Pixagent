```markdown
# Pixagent

AI-powered repair tracking for Pixel IT laptop shop.

Technicians manage tickets and leave progress notes. Customers look up their ticket and can chat with an assistant that only answers from real repair data — no guessing, no made-up updates.

Live frontend: https://srestho0101.github.io/Pixagent/frontend

---

## What it does

- Technician portal: login, create/edit/delete tickets, add repair notes, change status
- Customer side: enter a ticket ID → see current status + timeline of notes
- AI chat widget: customers can ask about their repair. The agent pulls from the database (and can fetch older logs if needed) and keeps answers short and honest

Statuses: `pending` → `in_progress` → `waiting_parts` → `completed`

---

## Stack

| Layer      | Tech                          |
|------------|-------------------------------|
| Backend    | FastAPI                       |
| Database   | Supabase (PostgreSQL)         |
| AI         | Mistral API (tool calling)    |
| Auth       | JWT + bcrypt                  |
| Frontend   | Plain HTML, CSS, JS           |

No frontend frameworks, no build step. Keeps things simple and free-tier friendly.

---

## Quick start

### 1. Clone & install

```bash
git clone https://github.com/Srestho0101/Pixagent.git
cd Pixagent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment

Copy the example and fill in the values:

```bash
cp .env.example .env
```

Required:

```env
DATABASE_URL=postgresql://...          # Supabase connection string
JWT_SECRET=some-long-random-string
MISTRAL_API_KEY=your_key_here
MISTRAL_MODEL=mistral-small-latest     # optional, this is the default
FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

### 3. Database

You need three tables. Run something like this in the Supabase SQL editor:

```sql
create table technicians (
  id serial primary key,
  email text unique not null,
  name text not null,
  password_hash text not null
);

create table tickets (
  id serial primary key,
  customer_name text not null,
  device_info text not null,
  status text not null default 'pending'
    check (status in ('pending', 'in_progress', 'waiting_parts', 'completed')),
  technician_id integer not null references technicians(id),
  created_at timestamptz not null default now()
);

create table repair_logs (
  id serial primary key,
  ticket_id integer not null references tickets(id),
  technician_id integer not null references technicians(id),
  note text not null,
  created_at timestamptz not null default now()
);

create index idx_logs_ticket on repair_logs (ticket_id, created_at desc);
```

### 4. Create a technician

```bash
python create_technician.py
```

(Edit the email/name/password inside the file first if you want.)

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

API will be at http://localhost:8000

### 6. Frontend

In another terminal:

```bash
python -m http.server 5500 --directory frontend
```

Open http://localhost:5500

The frontend talks to `http://localhost:8000/api` by default. You can override it by setting `window.PIXEL_BOT_API_URL` before `app.js` loads.

---

## Seed data for testing the agent

There’s a realistic multi-log ticket you can load:

```bash
python seed_agent_test_data.py
# or
python seed_agent_test_data.py --reset
```

It creates a Lenovo X1 Carbon job with a completed battery repair and a still-pending keyboard part. Useful for checking that the agent doesn’t mix the two up or invent details.

There’s also `agent_edge_case_prompts.md` with a list of questions that probe status, unknowns, contradictions, privacy, and prompt injection.

---

## API overview

| Method | Path                        | Who          | Purpose                          |
|--------|-----------------------------|--------------|----------------------------------|
| POST   | `/api/login`                | Tech         | Get JWT                          |
| POST   | `/api/tickets`              | Tech         | Create ticket                    |
| GET    | `/api/tickets/my`           | Tech         | List own tickets                 |
| PATCH  | `/api/tickets/{id}`         | Tech         | Update ticket                    |
| DELETE | `/api/tickets/{id}`         | Tech         | Delete ticket + its logs         |
| POST   | `/api/logs`                 | Tech         | Add progress note                |
| DELETE | `/api/logs/{id}`            | Tech         | Delete a note                    |
| GET    | `/api/tickets/{id}/logs`    | Customer     | Status + public history          |
| POST   | `/api/chat`                 | Customer     | Streaming AI chat (SSE)          |
| GET    | `/health`                   | Anyone       | Health check                     |

---

## How the AI works

The chat endpoint streams responses. For each message it:

1. Loads the ticket + recent logs into the system prompt
2. Sends the conversation to Mistral with one tool: `get_repair_logs`
3. If the model calls the tool, the backend runs the query and continues
4. Streams the final answer

Rules are strict: only use the verified ticket data, never invent updates, refuse other tickets, keep replies short. If Mistral rate-limits, a simple fallback kicks in using the same context.

---

## Project layout

```
app/
  main.py          # FastAPI app + CORS
  config.py
  database.py
  auth.py          # JWT + password hashing
  models.py        # Pydantic schemas
  agent.py         # Mistral + tool calling + streaming
  routes/
    auth.py
    tickets.py
    logs.py
    chat.py
frontend/          # Static UI (technician + customer views)
create_technician.py
seed_agent_test_data.py
plan.md            # Original design notes
agent_edge_case_prompts.md
```

---

## Notes

- Customer access is currently just “know the ticket ID”. Fine for a small shop; not enterprise-grade auth.
- Free tiers of Supabase + Mistral + a static host are enough to run this.
- The agent is deliberately conservative. If the logs don’t contain the answer, it says so instead of guessing.

That’s it. Open an issue or PR if you improve something.
```