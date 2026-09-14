# Database & Schema Thinking

## The Three Tables

```sql
technicians (id, email, name, password_hash)
tickets     (id, customer_name, device_info, status, technician_id, created_at)
repair_logs (id, ticket_id, technician_id, note, created_at)
```

Plus the index:

```sql
CREATE INDEX idx_logs_ticket ON repair_logs (ticket_id, created_at DESC);
```

## Why This Shape Works

- **Tickets** own the high-level state machine (`pending → in_progress → waiting_parts → completed`).
- **Logs** are an append-only timeline. They never overwrite history.
- **Technicians** are the only authenticated actors that mutate data.

The agent is allowed to *read* tickets + logs; it is never allowed to write.

## Design Lessons

1. **Status is a first-class column**, not derived from the latest log.  
   This prevents the model from declaring a ticket complete just because an old log said “tested OK”.

2. **Logs are chronological facts**.  
   The agent is taught to treat them as a timeline and to use the tool when it needs older entries.

3. **Ownership is enforced in SQL**, not only in the application layer.  
   Every mutating query includes `AND technician_id = %s`.

4. **Customer view is deliberately narrower**.  
   The public endpoint never returns technician IDs or internal fields.

## Scaling the Schema Later

- Add `updated_at` triggers if you need them.
- Add a `parts` / `orders` table when inventory becomes important.
- Consider soft-deletes (`deleted_at`) instead of hard deletes for auditability.
- Add RLS policies in Supabase as defense-in-depth (even if the API already checks ownership).

## Mental Model

The database is the single source of truth.  
The LLM is a *reader and explainer*, never a writer of business facts.  
That separation is what keeps the system trustworthy.
