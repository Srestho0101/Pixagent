const API_BASE_URL = (window.PIXEL_BOT_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "pixel-repair-technician-token";
const THEME_STORAGE_KEY = "pixel-repair-theme";
const TICKET_SESSION_KEY = "pixel-repair-customer-ticket";

const state = {
  selectedTicketId: null,
  editingTicketId: null,
  historyTicketId: null,
  chatStarted: false,
};

const elements = {
  navButtons: document.querySelectorAll("[data-view]"),
  views: document.querySelectorAll(".view"),
  themeToggle: document.querySelector("#theme-toggle"),
  themeIcon: document.querySelector(".theme-icon"),
  themeLabel: document.querySelector(".theme-label"),
  loginPanel: document.querySelector("#login-panel"),
  dashboardPanel: document.querySelector("#dashboard-panel"),
  loginForm: document.querySelector("#login-form"),
  loginMessage: document.querySelector("#login-message"),
  logoutButton: document.querySelector("#logout-button"),
  ticketForm: document.querySelector("#ticket-form"),
  ticketMessage: document.querySelector("#ticket-message"),
  ticketsMessage: document.querySelector("#tickets-message"),
  ticketList: document.querySelector("#ticket-list"),
  refreshTickets: document.querySelector("#refresh-tickets"),
  lookupForm: document.querySelector("#lookup-form"),
  ticketId: document.querySelector("#ticket-id"),
  lookupMessage: document.querySelector("#lookup-message"),
  customerResult: document.querySelector("#customer-result"),
  resultTicketId: document.querySelector("#result-ticket-id"),
  resultTitle: document.querySelector("#result-title"),
  resultStatus: document.querySelector("#result-status"),
  customerLogList: document.querySelector("#customer-log-list"),
  logDialog: document.querySelector("#log-dialog"),
  logForm: document.querySelector("#log-form"),
  logTicketId: document.querySelector("#log-ticket-id"),
  logNote: document.querySelector("#log-note"),
  logMessage: document.querySelector("#log-message"),
  closeLogDialog: document.querySelector("#close-log-dialog"),
  editDialog: document.querySelector("#edit-dialog"),
  editForm: document.querySelector("#edit-form"),
  editTicketId: document.querySelector("#edit-ticket-id"),
  editCustomerName: document.querySelector("#edit-customer-name"),
  editDeviceInfo: document.querySelector("#edit-device-info"),
  editStatus: document.querySelector("#edit-status"),
  editMessage: document.querySelector("#edit-message"),
  closeEditDialog: document.querySelector("#close-edit-dialog"),
  historyDialog: document.querySelector("#history-dialog"),
  historyTicketId: document.querySelector("#history-ticket-id"),
  historyMessage: document.querySelector("#history-message"),
  historyList: document.querySelector("#history-list"),
  closeHistoryDialog: document.querySelector("#close-history-dialog"),
  chatToggle: document.querySelector("#ai-chat-toggle"),
  chatWidget: document.querySelector("#ai-chat-widget"),
  chatClose: document.querySelector("#ai-chat-close"),
  chatContext: document.querySelector("#ai-chat-context"),
  chatMessages: document.querySelector("#ai-chat-messages"),
  chatForm: document.querySelector("#ai-chat-form"),
  chatInput: document.querySelector("#ai-chat-input"),
  chatMessage: document.querySelector("#ai-chat-message"),
};

function getSessionTicketId() {
  const value = Number(window.sessionStorage.getItem(TICKET_SESSION_KEY));
  return Number.isInteger(value) && value > 0 ? value : null;
}

function saveSessionTicketId(ticketId) {
  window.sessionStorage.setItem(TICKET_SESSION_KEY, String(ticketId));
  updateChatContext();
}

function clearSessionTicketId() {
  window.sessionStorage.removeItem(TICKET_SESSION_KEY);
  updateChatContext();
}

function updateChatContext() {
  const ticketId = getSessionTicketId();
  elements.chatContext.textContent = ticketId
    ? `Using ticket #${ticketId} from this session.`
    : "Enter a ticket ID in Track a repair first.";
}

function getPreferredTheme() {
  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (storedTheme === "light" || storedTheme === "dark") return storedTheme;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme, persist = false) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";
  elements.themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  elements.themeToggle.setAttribute("title", isDark ? "Switch to light mode" : "Switch to dark mode");
  elements.themeIcon.textContent = isDark ? "☀" : "☾";
  elements.themeLabel.textContent = isDark ? "Light mode" : "Dark mode";

  if (persist) {
    window.localStorage.setItem(THEME_STORAGE_KEY, isDark ? "dark" : "light");
  }
}

function getToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

function saveToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

function clearToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function setMessage(element, message = "", type = "") {
  element.textContent = message;
  element.className = `form-message${type ? ` ${type}` : ""}`;
}

function setInlineMessage(element, message = "", type = "") {
  element.textContent = message;
  element.className = `inline-message${type ? ` ${type}` : ""}`;
}

function setLoading(form, loading) {
  form.classList.toggle("is-loading", loading);
  form.querySelectorAll("button").forEach((button) => {
    button.disabled = loading;
  });
}

function formatDate(value) {
  if (!value) return "Date unavailable";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function formatStatus(status) {
  return String(status || "unknown").replaceAll("_", " ");
}

function makeStatusBadge(status) {
  const badge = document.createElement("span");
  const safeStatus = String(status || "unknown").toLowerCase().replace(/[^a-z_]/g, "");
  badge.className = `status-badge ${safeStatus || "unknown"}`;
  badge.textContent = formatStatus(status);
  return badge;
}

async function apiRequest(path, { auth = true, ...options } = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token && auth) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error("Could not reach the repair service. Check that the backend is running.");
  }

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    if (response.status === 401 && auth) {
      clearToken();
      showLoggedOutState();
    }

    const detail = payload && typeof payload.detail === "string" ? payload.detail : "Something went wrong.";
    throw new Error(detail);
  }

  return payload;
}

function showLoggedOutState() {
  elements.loginPanel.classList.remove("hidden");
  elements.dashboardPanel.classList.add("hidden");
  elements.loginForm.reset();
}

function showLoggedInState() {
  elements.loginPanel.classList.add("hidden");
  elements.dashboardPanel.classList.remove("hidden");
  loadTickets();
}

function showView(viewId) {
  elements.views.forEach((view) => {
    const active = view.id === viewId;
    view.classList.toggle("active", active);
    view.hidden = !active;
  });

  elements.navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewId);
  });
}

function renderTickets(tickets) {
  elements.ticketList.replaceChildren();

  if (!tickets.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No tickets yet. Create the first repair to start your queue.";
    elements.ticketList.append(empty);
    return;
  }

  tickets.forEach((ticket) => {
    const card = document.createElement("article");
    card.className = "ticket-card";

    const content = document.createElement("div");
    const title = document.createElement("h3");
    title.textContent = ticket.customer_name || "Unnamed customer";

    const device = document.createElement("p");
    device.textContent = ticket.device_info || "Device details unavailable";

    const meta = document.createElement("div");
    meta.className = "ticket-meta";

    const ticketId = document.createElement("span");
    ticketId.className = "ticket-id";
    ticketId.textContent = `#${ticket.id}`;

    const created = document.createElement("span");
    created.className = "ticket-id";
    created.textContent = formatDate(ticket.created_at);

    meta.append(ticketId, makeStatusBadge(ticket.status), created);
    content.append(title, device, meta);

    const actions = document.createElement("div");
    actions.className = "ticket-actions";

    const addLogButton = document.createElement("button");
    addLogButton.className = "card-action";
    addLogButton.type = "button";
    addLogButton.textContent = "Add log";
    addLogButton.addEventListener("click", () => openLogDialog(ticket.id));

    const historyButton = document.createElement("button");
    historyButton.className = "card-action";
    historyButton.type = "button";
    historyButton.textContent = "View logs";
    historyButton.addEventListener("click", () => openHistoryDialog(ticket.id));

    const editButton = document.createElement("button");
    editButton.className = "card-action";
    editButton.type = "button";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", () => openEditDialog(ticket));

    const deleteButton = document.createElement("button");
    deleteButton.className = "card-action danger-action";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteTicket(ticket));

    actions.append(addLogButton, historyButton, editButton, deleteButton);
    card.append(content, actions);
    elements.ticketList.append(card);
  });
}

async function loadTickets() {
  setInlineMessage(elements.ticketsMessage, "Loading tickets...");

  try {
    const tickets = await apiRequest("/tickets/my");
    renderTickets(Array.isArray(tickets) ? tickets : []);
    setInlineMessage(elements.ticketsMessage, `${tickets.length} ticket${tickets.length === 1 ? "" : "s"}`);
  } catch (error) {
    setInlineMessage(elements.ticketsMessage, error.message, "error");
  }
}

function openEditDialog(ticket) {
  state.editingTicketId = ticket.id;
  elements.editTicketId.textContent = ticket.id;
  elements.editCustomerName.value = ticket.customer_name || "";
  elements.editDeviceInfo.value = ticket.device_info || "";
  elements.editStatus.value = ticket.status || "pending";
  setMessage(elements.editMessage);

  if (typeof elements.editDialog.showModal === "function") {
    elements.editDialog.showModal();
  } else {
    elements.editDialog.setAttribute("open", "");
  }

  elements.editCustomerName.focus();
}

function closeEditDialog() {
  if (typeof elements.editDialog.close === "function") {
    elements.editDialog.close();
  } else {
    elements.editDialog.removeAttribute("open");
  }
  state.editingTicketId = null;
}

async function handleEditTicket(event) {
  event.preventDefault();
  if (!state.editingTicketId) return;

  setMessage(elements.editMessage);
  setLoading(elements.editForm, true);

  const formData = new FormData(elements.editForm);
  try {
    await apiRequest(`/tickets/${state.editingTicketId}`, {
      method: "PATCH",
      body: JSON.stringify({
        customer_name: formData.get("customer_name"),
        device_info: formData.get("device_info"),
        status: formData.get("status"),
      }),
    });

    const editedTicketId = state.editingTicketId;
    closeEditDialog();
    await loadTickets();
    setInlineMessage(elements.ticketsMessage, `Ticket #${editedTicketId} updated.`, "success");
  } catch (error) {
    setMessage(elements.editMessage, error.message, "error");
  } finally {
    setLoading(elements.editForm, false);
  }
}

async function deleteTicket(ticket) {
  const confirmed = window.confirm(
    `Delete ticket #${ticket.id} for ${ticket.customer_name}? This will also permanently delete its repair logs.`,
  );
  if (!confirmed) return;

  setInlineMessage(elements.ticketsMessage, `Deleting ticket #${ticket.id}...`);
  try {
    await apiRequest(`/tickets/${ticket.id}`, { method: "DELETE" });
    await loadTickets();
    setInlineMessage(elements.ticketsMessage, `Ticket #${ticket.id} deleted.`, "success");
  } catch (error) {
    setInlineMessage(elements.ticketsMessage, error.message, "error");
  }
}

function openHistoryDialog(ticketId) {
  state.historyTicketId = ticketId;
  elements.historyTicketId.textContent = ticketId;
  elements.historyList.replaceChildren();
  setInlineMessage(elements.historyMessage, "Loading logs...");

  if (typeof elements.historyDialog.showModal === "function") {
    elements.historyDialog.showModal();
  } else {
    elements.historyDialog.setAttribute("open", "");
  }

  loadHistoryLogs();
}

function closeHistoryDialog() {
  if (typeof elements.historyDialog.close === "function") {
    elements.historyDialog.close();
  } else {
    elements.historyDialog.removeAttribute("open");
  }
  state.historyTicketId = null;
}

function renderHistoryLogs(logs) {
  elements.historyList.replaceChildren();

  if (!logs.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No repair logs have been added to this ticket.";
    elements.historyList.append(empty);
    return;
  }

  logs.forEach((log) => {
    const item = document.createElement("article");
    item.className = "history-item";

    const content = document.createElement("div");
    const time = document.createElement("time");
    time.dateTime = log.created_at || "";
    time.textContent = formatDate(log.created_at);

    const note = document.createElement("p");
    note.textContent = log.note || "No note provided.";
    content.append(time, note);

    const deleteButton = document.createElement("button");
    deleteButton.className = "card-action danger-action";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteLog(log));

    item.append(content, deleteButton);
    elements.historyList.append(item);
  });
}

async function loadHistoryLogs() {
  if (!state.historyTicketId) return;

  try {
    const result = await apiRequest(`/tickets/${state.historyTicketId}/logs`);
    renderHistoryLogs(Array.isArray(result.logs) ? result.logs : []);
    const count = Array.isArray(result.logs) ? result.logs.length : 0;
    setInlineMessage(elements.historyMessage, `${count} log${count === 1 ? "" : "s"}`);
  } catch (error) {
    setInlineMessage(elements.historyMessage, error.message, "error");
  }
}

async function deleteLog(log) {
  const confirmed = window.confirm("Delete this repair log permanently?");
  if (!confirmed) return;

  try {
    await apiRequest(`/logs/${log.id}`, { method: "DELETE" });
    await loadHistoryLogs();
  } catch (error) {
    setInlineMessage(elements.historyMessage, error.message, "error");
  }
}

async function handleLogin(event) {
  event.preventDefault();
  setMessage(elements.loginMessage);
  setLoading(elements.loginForm, true);

  const formData = new FormData(elements.loginForm);
  try {
    const result = await apiRequest("/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });

    if (!result || !result.access_token) {
      throw new Error("The server returned an invalid login response.");
    }

    saveToken(result.access_token);
    setMessage(elements.loginMessage, "Signed in successfully.", "success");
    showLoggedInState();
  } catch (error) {
    setMessage(elements.loginMessage, error.message, "error");
  } finally {
    setLoading(elements.loginForm, false);
  }
}

async function handleCreateTicket(event) {
  event.preventDefault();
  setMessage(elements.ticketMessage);
  setLoading(elements.ticketForm, true);

  const formData = new FormData(elements.ticketForm);
  try {
    const ticket = await apiRequest("/tickets", {
      method: "POST",
      body: JSON.stringify({
        customer_name: formData.get("customer_name"),
        device_info: formData.get("device_info"),
      }),
    });

    elements.ticketForm.reset();
    setMessage(elements.ticketMessage, `Ticket #${ticket.id} created.`, "success");
    await loadTickets();
  } catch (error) {
    setMessage(elements.ticketMessage, error.message, "error");
  } finally {
    setLoading(elements.ticketForm, false);
  }
}

function openLogDialog(ticketId) {
  state.selectedTicketId = ticketId;
  elements.logTicketId.textContent = ticketId;
  elements.logForm.reset();
  setMessage(elements.logMessage);

  if (typeof elements.logDialog.showModal === "function") {
    elements.logDialog.showModal();
  } else {
    elements.logDialog.setAttribute("open", "");
  }

  elements.logNote.focus();
}

function closeLogDialog() {
  if (typeof elements.logDialog.close === "function") {
    elements.logDialog.close();
  } else {
    elements.logDialog.removeAttribute("open");
  }
  state.selectedTicketId = null;
}

async function handleCreateLog(event) {
  event.preventDefault();
  if (!state.selectedTicketId) return;

  setMessage(elements.logMessage);
  setLoading(elements.logForm, true);

  const formData = new FormData(elements.logForm);
  try {
    await apiRequest("/logs", {
      method: "POST",
      body: JSON.stringify({
        ticket_id: state.selectedTicketId,
        note: formData.get("note"),
      }),
    });

    closeLogDialog();
    await loadTickets();
  } catch (error) {
    setMessage(elements.logMessage, error.message, "error");
  } finally {
    setLoading(elements.logForm, false);
  }
}

function renderCustomerResult(result) {
  elements.resultTicketId.textContent = result.ticket_id;
  elements.resultTitle.textContent = "Repair updates";
  const safeStatus = String(result.status || "unknown").toLowerCase().replace(/[^a-z_]/g, "");
  elements.resultStatus.className = `status-badge ${safeStatus || "unknown"}`;
  elements.resultStatus.textContent = formatStatus(result.status);
  elements.customerLogList.replaceChildren();

  if (!result.logs || !result.logs.length) {
    const empty = document.createElement("p");
    empty.className = "no-logs";
    empty.textContent = "No technician updates have been added yet. Please check back soon.";
    elements.customerLogList.append(empty);
  } else {
    result.logs.forEach((log) => {
      const item = document.createElement("article");
      item.className = "customer-log";

      const time = document.createElement("time");
      time.dateTime = log.created_at || "";
      time.textContent = formatDate(log.created_at);

      const note = document.createElement("p");
      note.textContent = log.note || "No note provided.";

      item.append(time, note);
      elements.customerLogList.append(item);
    });
  }

  elements.customerResult.classList.remove("hidden");
}

async function handleCustomerLookup(event) {
  event.preventDefault();
  setMessage(elements.lookupMessage);
  setLoading(elements.lookupForm, true);

  const formData = new FormData(elements.lookupForm);
  const ticketId = Number(formData.get("ticket_id"));

  if (!Number.isInteger(ticketId) || ticketId < 1) {
    setMessage(elements.lookupMessage, "Enter a valid ticket ID.", "error");
    setLoading(elements.lookupForm, false);
    return;
  }

  try {
    const result = await apiRequest(`/tickets/${ticketId}/logs`, { auth: false });
    saveSessionTicketId(ticketId);
    renderCustomerResult(result);
    setMessage(elements.lookupMessage, "Latest repair information loaded.", "success");
  } catch (error) {
    clearSessionTicketId();
    elements.customerResult.classList.add("hidden");
    setMessage(elements.lookupMessage, error.message, "error");
  } finally {
    setLoading(elements.lookupForm, false);
  }
}

function appendChatMessage(role, message = "") {
  const bubble = document.createElement("div");
  bubble.className = `ai-chat-bubble ${role}`;
  bubble.textContent = message;
  elements.chatMessages.append(bubble);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  return bubble;
}

function openChatWidget() {
  elements.chatWidget.classList.remove("hidden");
  elements.chatToggle.setAttribute("aria-expanded", "true");
  elements.chatToggle.setAttribute("aria-label", "Close repair assistant");

  if (!state.chatStarted) {
    const ticketId = getSessionTicketId();
    appendChatMessage(
      "assistant",
      ticketId
        ? `Hi! I can help with ticket #${ticketId}. What would you like to know?`
        : "Hi! Enter a ticket ID in Track a repair first, then I can answer questions about its repair.",
    );
    state.chatStarted = true;
  }

  updateChatContext();
  elements.chatInput.focus();
}

function closeChatWidget() {
  elements.chatWidget.classList.add("hidden");
  elements.chatToggle.setAttribute("aria-expanded", "false");
  elements.chatToggle.setAttribute("aria-label", "Open repair assistant");
}

function handleChatStreamEvent(rawEvent, assistantBubble) {
  const dataLine = rawEvent
    .split("\n")
    .find((line) => line.startsWith("data:"));
  if (!dataLine) return false;

  const data = dataLine.slice(5).trim();
  if (data === "[DONE]") return true;

  const payload = JSON.parse(data);
  if (payload.error) {
    assistantBubble.textContent = payload.error;
    setMessage(elements.chatMessage, payload.error, "error");
    return false;
  }

  if (payload.content) {
    assistantBubble.textContent += payload.content;
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
  return false;
}

async function handleChat(event) {
  event.preventDefault();
  const message = elements.chatInput.value.trim();
  if (!message) return;

  appendChatMessage("user", message);
  elements.chatInput.value = "";
  setMessage(elements.chatMessage);
  setLoading(elements.chatForm, true);

  const assistantBubble = appendChatMessage("assistant", "");
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ticket_id: getSessionTicketId(),
        message,
      }),
    });

    if (!response.ok) {
      let detail = "The repair assistant could not process that message.";
      try {
        const payload = await response.json();
        if (typeof payload.detail === "string") detail = payload.detail;
      } catch {
        // Keep the friendly fallback above when the server has no JSON error.
      }
      throw new Error(detail);
    }

    if (!response.body) throw new Error("The repair assistant returned an empty response.");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finished = false;

    while (!finished) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const rawEvent of events) {
        if (handleChatStreamEvent(rawEvent, assistantBubble)) finished = true;
      }
      if (done) break;
    }

    if (buffer.trim()) handleChatStreamEvent(buffer, assistantBubble);
    if (!assistantBubble.textContent) {
      assistantBubble.textContent = "I don't have an update for that yet.";
    }
  } catch (error) {
    assistantBubble.textContent = error.message;
    setMessage(elements.chatMessage, error.message, "error");
  } finally {
    setLoading(elements.chatForm, false);
    elements.chatInput.focus();
  }
}

elements.navButtons.forEach((button) => {
  button.addEventListener("click", () => showView(button.dataset.view));
});

applyTheme(getPreferredTheme());
elements.themeToggle.addEventListener("click", () => {
  const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme, true);
});

elements.loginForm.addEventListener("submit", handleLogin);
elements.logoutButton.addEventListener("click", () => {
  clearToken();
  showLoggedOutState();
  setMessage(elements.loginMessage, "You have been signed out.", "success");
});
elements.ticketForm.addEventListener("submit", handleCreateTicket);
elements.refreshTickets.addEventListener("click", loadTickets);
elements.lookupForm.addEventListener("submit", handleCustomerLookup);
elements.logForm.addEventListener("submit", handleCreateLog);
elements.closeLogDialog.addEventListener("click", closeLogDialog);
elements.logDialog.addEventListener("click", (event) => {
  if (event.target === elements.logDialog) closeLogDialog();
});
elements.editForm.addEventListener("submit", handleEditTicket);
elements.closeEditDialog.addEventListener("click", closeEditDialog);
elements.editDialog.addEventListener("click", (event) => {
  if (event.target === elements.editDialog) closeEditDialog();
});
elements.closeHistoryDialog.addEventListener("click", closeHistoryDialog);
elements.historyDialog.addEventListener("click", (event) => {
  if (event.target === elements.historyDialog) closeHistoryDialog();
});
elements.chatToggle.addEventListener("click", () => {
  if (elements.chatWidget.classList.contains("hidden")) openChatWidget();
  else closeChatWidget();
});
elements.chatClose.addEventListener("click", closeChatWidget);
elements.chatForm.addEventListener("submit", handleChat);

const sessionTicketId = getSessionTicketId();
if (sessionTicketId) elements.ticketId.value = sessionTicketId;
updateChatContext();

if (getToken()) {
  showLoggedInState();
}
