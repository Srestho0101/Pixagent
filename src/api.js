import { state } from './state.js';

// Keep transport concerns here. Views only call domain methods, so backend wiring
// can be changed without touching templates or event handlers.
const useBackend = true;

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${api.API_URL}${path}`, {
    headers,
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

export const api = {
  API_URL: window.FIXFLOW_API_URL || 'http://localhost:8000',
  async login(email, password) {
    if (useBackend) {
      const session = await request('/api/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      state.token = session.access_token;
      localStorage.setItem('fixflow_token', session.access_token);
      return session;
    }
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
  async getPublicTicket(ticketId) {
    if (useBackend) return request(`/api/tickets/${encodeURIComponent(ticketId)}`);
    return state.tickets.find(({ id }) => id === ticketId);
  },
  async chat(ticketId, message) {
    if (useBackend) {
      const response = await fetch(`${api.API_URL}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ticket_id: ticketId, message }) });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${response.status})`);
      }
      return response;
    }
    return { ticketId, message };
  },
};
