import { state } from './state.js';

// Keep transport concerns here. Views only call domain methods, so backend wiring
// can be changed without touching templates or event handlers.
const useBackend = false;

async function request(path, options = {}) {
  const response = await fetch(`${api.API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

export const api = {
  API_URL: 'http://localhost:8000',
  async login(email, password) {
    if (useBackend) return request('/api/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    return { email, password };
  },
  async getTickets() {
    if (useBackend) return request('/api/tickets/my');
    return state.tickets;
  },
  async createTicket(ticket) {
    if (useBackend) return request('/api/tickets', { method: 'POST', body: JSON.stringify(ticket) });
    state.tickets.unshift(ticket);
    return ticket;
  },
  async addLog(ticketId, note) {
    if (useBackend) return request('/api/logs', { method: 'POST', body: JSON.stringify({ ticket_id: ticketId, note }) });
    return { ticketId, note };
  },
  async chat(ticketId, message) {
    if (useBackend) return request('/api/chat', { method: 'POST', body: JSON.stringify({ ticket_id: ticketId, message }) });
    return { ticketId, message };
  },
};
