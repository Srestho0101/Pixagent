const API_BASE_URL = (window.PIXEL_BOT_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
const TOKEN_STORAGE_KEY = "pixel-repair-technician-token";
const THEME_STORAGE_KEY = "pixel-repair-theme";

const state = {
  selectedTicketId: null,
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
};

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

    const addLogButton = document.createElement("button");
    addLogButton.className = "card-action";
    addLogButton.type = "button";
    addLogButton.textContent = "Add log";
    addLogButton.addEventListener("click", () => openLogDialog(ticket.id));

    card.append(content, addLogButton);
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
    renderCustomerResult(result);
    setMessage(elements.lookupMessage, "Latest repair information loaded.", "success");
  } catch (error) {
    elements.customerResult.classList.add("hidden");
    setMessage(elements.lookupMessage, error.message, "error");
  } finally {
    setLoading(elements.lookupForm, false);
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

if (getToken()) {
  showLoggedInState();
}
