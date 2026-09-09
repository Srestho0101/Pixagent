-- FixFlow initial schema. Run this file in the Supabase SQL editor before
-- starting the API. The FastAPI service must use a server-only secret key.

create table if not exists public.technicians (
  id bigint generated always as identity primary key,
  email text not null unique check (email = lower(email)),
  name text not null check (char_length(trim(name)) between 1 and 120),
  password_hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.tickets (
  id bigint generated always as identity primary key,
  public_id text not null unique check (public_id ~ '^RF-[0-9]{6}$'),
  customer_name text not null check (char_length(trim(customer_name)) between 1 and 120),
  device_info text not null check (char_length(trim(device_info)) between 1 and 240),
  status text not null default 'pending'
    check (status in ('pending', 'in_progress', 'waiting_parts', 'completed')),
  technician_id bigint not null references public.technicians(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.repair_logs (
  id bigint generated always as identity primary key,
  ticket_id bigint not null references public.tickets(id) on delete cascade,
  technician_id bigint not null references public.technicians(id) on delete restrict,
  note text not null check (char_length(trim(note)) between 1 and 2000),
  created_at timestamptz not null default now()
);

-- Covers the dashboard query, public ticket lookup, and latest-log lookup.
create index if not exists tickets_technician_created_idx
  on public.tickets (technician_id, created_at desc);
create index if not exists repair_logs_ticket_created_idx
  on public.repair_logs (ticket_id, created_at desc);
create index if not exists repair_logs_technician_idx
  on public.repair_logs (technician_id);

-- The API is the only data-access boundary. The server's secret/service key
-- bypasses RLS; browser clients have neither grants nor an RLS policy.
alter table public.technicians enable row level security;
alter table public.tickets enable row level security;
alter table public.repair_logs enable row level security;
alter table public.technicians force row level security;
alter table public.tickets force row level security;
alter table public.repair_logs force row level security;

revoke all on public.technicians, public.tickets, public.repair_logs from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;

-- Create the first technician using a bcrypt hash generated locally, then run:
-- insert into public.technicians (email, name, password_hash)
-- values ('tech@example.com', 'Technician Name', '$2b$...');
