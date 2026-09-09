# FixFlow

FixFlow is a vanilla-JS repair-shop frontend backed by FastAPI, Supabase Postgres, and Mistral tool calling.

## One-time database setup

1. In the Supabase dashboard, open **SQL Editor** and run [`database/001_initial_schema.sql`](database/001_initial_schema.sql).
2. Generate a technician password hash:

   ```bash
   .venv/bin/python scripts/create_password_hash.py
   ```

3. Insert the resulting hash in the SQL editor:

   ```sql
   insert into public.technicians (email, name, password_hash)
   values ('tech@fixflow.test', 'FixFlow Technician', '$2b$...');
   ```

The migration enables RLS and revokes browser roles. The API must therefore use a server-only Supabase secret key (`sb_secret_...`) or legacy `service_role` key—never a publishable/anon key.

## Configuration

Copy the missing values from [`.env.example`](.env.example) into `.env`. Your existing `MISTRAL_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` are already recognized. Add a stable random `JWT_SECRET`, for example:

```bash
openssl rand -hex 32
```

Set `FRONTEND_ORIGINS` to the exact local and deployed frontend URLs. For a deployed static frontend, set its backend URL before loading `src/main.js`:

```html
<script>window.FIXFLOW_API_URL = 'https://your-api.example.com';</script>
```

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn backend.main:app --reload
```

Serve the project root with any static server, for example:

```bash
python3 -m http.server 5500
```

Then visit `http://localhost:5500`. The API health check is at `http://localhost:8000/health`.

## API

- `POST /api/login` authenticates a technician and returns a 24-hour JWT.
- `GET /api/tickets/my`, `POST /api/tickets`, and `POST /api/logs` require that JWT.
- `GET /api/tickets/{ticket_id}` returns only customer-safe fields for the lookup screen.
- `POST /api/chat` streams a Mistral response as plain text. Mistral can call `get_ticket_status` and `get_recent_logs`; those tools are confined to the ticket in the request.
