-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Technicians table
CREATE TABLE IF NOT EXISTS technicians (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    device_info TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'in_progress', 'waiting_parts', 'completed')),
    technician_id INTEGER NOT NULL REFERENCES technicians(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Repair logs table
CREATE TABLE IF NOT EXISTS repair_logs (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    technician_id INTEGER NOT NULL REFERENCES technicians(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tickets_technician ON tickets(technician_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_ticket ON repair_logs(ticket_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);

-- Row Level Security (RLS)
ALTER TABLE technicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE repair_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for technicians
CREATE POLICY "Technicians can view their own data" ON technicians
    FOR SELECT USING (id = current_setting('request.jwt.claims', true)::json->>'sub');

-- RLS Policies for tickets
CREATE POLICY "Technicians can view their own tickets" ON tickets
    FOR SELECT USING (technician_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Technicians can insert their own tickets" ON tickets
    FOR INSERT WITH CHECK (technician_id = current_setting('request.jwt.claims', true)::json->>'sub');

CREATE POLICY "Technicians can update their own tickets" ON tickets
    FOR UPDATE USING (technician_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- RLS Policies for repair_logs
CREATE POLICY "Technicians can view logs for their tickets" ON repair_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tickets 
            WHERE tickets.id = repair_logs.ticket_id 
            AND tickets.technician_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
    );

CREATE POLICY "Technicians can insert logs for their tickets" ON repair_logs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM tickets 
            WHERE tickets.id = repair_logs.ticket_id 
            AND tickets.technician_id = current_setting('request.jwt.claims', true)::json->>'sub'
        )
    );

-- Create a function to hash passwords (for initial setup)
CREATE OR REPLACE FUNCTION hash_password(password TEXT) 
RETURNS TEXT AS $$
BEGIN
    RETURN crypt(password, gen_salt('bf'));
END;
$$ LANGUAGE plpgsql;