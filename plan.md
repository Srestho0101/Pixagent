# Laptop Repair Shop AI Agent System - Brief Plan

## 1. Overview
A minimal cloud-based system where:
- **Technicians** create tickets and add progress logs from any device
- **Customers** chat with an AI agent to check repair status
- **Agent** uses tool calling (fast DB lookups, not RAG) for accurate responses

---

## 2. Architecture

```
Technician UI (HTML/CSS/JS)  ─┐
                              ├──► FastAPI Backend ──► Supabase (PostgreSQL)
Customer Chat UI (HTML/CSS/JS)─┘         │
                                          ▼
                                    Mistral AI API
                                    (Tool Calling)
```

---

## 3. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML/CSS/JS |
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL, free tier) |
| AI | Mistral API (free credits) |
| Auth | JWT tokens |
| Hosting | Railway (backend) + Vercel (frontend) |

---

## 4. Database Schema (3 Tables)

```sql
technicians (id, email, name, password_hash)
tickets (id, customer_name, device_info, status, technician_id, created_at)
repair_logs (id, ticket_id, technician_id, note, created_at)
```

**Indexes**: `idx_logs_ticket ON repair_logs(ticket_id, created_at DESC)`

---

## 5. API Endpoints (5 Total)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/login` | Technician login → JWT token |
| POST | `/api/tickets` | Create new repair ticket |
| GET | `/api/tickets/my` | List technician's tickets |
| POST | `/api/logs` | Add technician note |
| POST | `/api/chat` | Customer AI chat (streaming) |

---

## 6. Agent Logic (Mistral Tool Calling)

### System Prompt Template
```
You're a repair shop assistant. Ticket status: {status}, Device: {device}.

Recent logs:
{logs_text}

Rules:
- Greetings → reply warmly
- Progress questions → use logs
- Never guess → only use logs
- If unknown → say "I don't have that info yet"
- Keep replies to 2-3 sentences
```

### Tools Defined
1. **get_recent_logs(ticket_id, limit=5)** → Fetches latest technician notes
2. **get_ticket_status(ticket_id)** → Fetches current status

### Flow
1. Customer sends message
2. Agent fetches logs + status (context)
3. Mistral decides: use tool? reply directly?
4. If tool called → execute SQL query → return to Mistral
5. Stream final response to customer

---

## 7. User Interface

### Technician Dashboard
- Login screen (email/password)
- Ticket list with status badges (pending/in_progress/waiting_parts/completed)
- "New Ticket" button (modal)
- "Add Log" button (modal/prompt)

### Customer Chat
- Ticket ID input screen
- Chat interface with message bubbles
- Streaming responses (real-time)
- Status displayed in header

---

## 8. Implementation Timeline (8 Days)

| Phase | Duration | Tasks |
|-------|----------|-------|
| Setup | Day 1 | Supabase project, SQL schema, environment |
| Backend | Days 2-3 | Login, tickets, logs endpoints |
| Agent | Day 4 | Mistral integration, tools, streaming |
| Frontend | Days 5-6 | Technician UI + Customer chat UI |
| Testing | Day 7 | End-to-end flows, edge cases |
| Deploy | Day 8 | Railway + Vercel, production test |

---

## 9. Costs (First Month)

| Service | Cost |
|---------|------|
| Supabase | Free |
| Mistral API | Free credits |
| Railway | Free tier |
| Vercel | Free tier |
| **Total** | **$0** |

---

## 10. Security

- JWT tokens (24h expiry)
- bcrypt password hashing
- Row-Level Security (RLS) in Supabase
- Environment variables for secrets

---

## 11. Key Benefits

- ✅ **Fast**: Tool calling = <10ms DB lookups
- ✅ **Accurate**: No hallucinated vector matches
- ✅ **Multi-device**: Cloud database syncs technicians
- ✅ **Minimal**: No frameworks, no build tools
- ✅ **Free**: Start with $0 cost

---

## 12. Future Enhancements (Optional)

- Real-time updates (Supabase Realtime)
- Email/SMS notifications
- Multi-language support
- Photo uploads for repairs
- Technician analytics dashboard