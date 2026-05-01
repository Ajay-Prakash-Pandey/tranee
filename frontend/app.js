const tokenKey = "assignment_demo_token";
const userKey = "assignment_demo_user";

const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");
const taskForm = document.getElementById("taskForm");
const logoutBtn = document.getElementById("logoutBtn");
const refreshTasksBtn = document.getElementById("refreshTasksBtn");
const clearTaskBtn = document.getElementById("clearTaskBtn");
const loadAdminBtn = document.getElementById("loadAdminBtn");

const flashMessage = document.getElementById("flashMessage");
const sessionInfo = document.getElementById("sessionInfo");
const taskList = document.getElementById("taskList");
const adminSummary = document.getElementById("adminSummary");
const adminUsers = document.getElementById("adminUsers");

registerForm.addEventListener("submit", handleRegister);
loginForm.addEventListener("submit", handleLogin);
taskForm.addEventListener("submit", handleTaskSubmit);
logoutBtn.addEventListener("click", logout);
refreshTasksBtn.addEventListener("click", loadTasks);
clearTaskBtn.addEventListener("click", clearTaskForm);
loadAdminBtn.addEventListener("click", loadAdminData);

restoreSession();

async function handleRegister(event) {
  event.preventDefault();

  const payload = {
    name: document.getElementById("registerName").value.trim(),
    email: document.getElementById("registerEmail").value.trim(),
    password: document.getElementById("registerPassword").value,
    role: document.getElementById("registerRole").value
  };

  const result = await request("/api/v1/auth/register", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload)
  });

  if (result.ok) {
    registerForm.reset();
    showFlash(result.data.message, "success");
  } else {
    showFlash(extractError(result.data), "error");
  }
}

async function handleLogin(event) {
  event.preventDefault();

  const payload = {
    email: document.getElementById("loginEmail").value.trim(),
    password: document.getElementById("loginPassword").value
  };

  const result = await request("/api/v1/auth/login", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload)
  });

  if (!result.ok) {
    showFlash(extractError(result.data), "error");
    return;
  }

  localStorage.setItem(tokenKey, result.data.data.access_token);
  localStorage.setItem(userKey, JSON.stringify(result.data.data.user));
  loginForm.reset();
  showFlash("Login successful. Protected APIs are now available.", "success");
  restoreSession();
}

async function handleTaskSubmit(event) {
  event.preventDefault();

  const token = getToken();
  if (!token) {
    showFlash("Please log in before managing tasks.", "error");
    return;
  }

  const taskId = document.getElementById("taskId").value;
  const payload = {
    title: document.getElementById("taskTitle").value.trim(),
    description: document.getElementById("taskDescription").value.trim(),
    status: document.getElementById("taskStatus").value,
    priority: document.getElementById("taskPriority").value,
    due_date: document.getElementById("taskDueDate").value || null
  };

  const endpoint = taskId ? `/api/v1/tasks/${taskId}` : "/api/v1/tasks";
  const method = taskId ? "PUT" : "POST";
  const result = await request(endpoint, {
    method,
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });

  if (!result.ok) {
    showFlash(extractError(result.data), "error");
    return;
  }

  showFlash(result.data.message, "success");
  clearTaskForm();
  loadTasks();
}

async function loadTasks() {
  const token = getToken();
  if (!token) {
    taskList.className = "task-list empty-state";
    taskList.textContent = "Login to load tasks.";
    return;
  }

  const result = await request("/api/v1/tasks", {
    method: "GET",
    headers: authHeaders(token)
  });

  if (!result.ok) {
    showFlash(extractError(result.data), "error");
    return;
  }

  const tasks = result.data.data.tasks;
  renderTasks(tasks);
}

async function loadAdminData() {
  const token = getToken();
  const user = getUser();

  if (!token || !user) {
    showFlash("Please log in first.", "error");
    return;
  }

  if (user.role !== "admin") {
    showFlash("Only admins can access the admin panel.", "error");
    return;
  }

  const [summaryResult, usersResult] = await Promise.all([
    request("/api/v1/auth/admin/summary", { method: "GET", headers: authHeaders(token) }),
    request("/api/v1/auth/admin/users", { method: "GET", headers: authHeaders(token) })
  ]);

  if (!summaryResult.ok) {
    showFlash(extractError(summaryResult.data), "error");
    return;
  }

  if (!usersResult.ok) {
    showFlash(extractError(usersResult.data), "error");
    return;
  }

  renderSummary(summaryResult.data.data.counts);
  renderUsers(usersResult.data.data.users);
}

function restoreSession() {
  const user = getUser();
  if (!user || !getToken()) {
    sessionInfo.innerHTML = "<p class='session-empty'>No active session.</p>";
    taskList.className = "task-list empty-state";
    taskList.textContent = "Login to load tasks.";
    adminSummary.className = "empty-state";
    adminSummary.textContent = "Admin-only metrics will appear here.";
    adminUsers.className = "user-list empty-state";
    adminUsers.textContent = "Admin-only user list will appear here.";
    return;
  }

  sessionInfo.innerHTML = `
    <div class="user-item">
      <h3>${escapeHtml(user.name)}</h3>
      <p>${escapeHtml(user.email)}</p>
      <span class="user-pill">${escapeHtml(user.role)}</span>
    </div>
  `;
  loadTasks();
  if (user.role === "admin") {
    loadAdminData();
  }
}

function renderTasks(tasks) {
  if (!tasks.length) {
    taskList.className = "task-list empty-state";
    taskList.textContent = "No tasks found yet. Create your first task.";
    return;
  }

  taskList.className = "task-list";
  taskList.innerHTML = tasks.map((task) => `
    <article class="task-item">
      <div class="task-top">
        <div>
          <h3>${escapeHtml(task.title)}</h3>
          <p>${escapeHtml(task.description || "No description provided.")}</p>
        </div>
        <div class="task-actions">
          <button type="button" class="secondary" onclick="populateTaskForm(${task.id})">Edit</button>
          <button type="button" onclick="deleteTask(${task.id})">Delete</button>
        </div>
      </div>
      <div class="task-meta">
        <span>Status: ${escapeHtml(task.status)}</span>
        <span>Priority: ${escapeHtml(task.priority)}</span>
        <span>Due: ${escapeHtml(task.due_date || "Not set")}</span>
        <span>Owner ID: ${task.owner_id}</span>
      </div>
    </article>
  `).join("");
}

function renderSummary(counts) {
  adminSummary.className = "";
  adminSummary.innerHTML = `
    <div class="summary-grid">
      <div class="summary-card"><span>Total Users</span><strong>${counts.users}</strong></div>
      <div class="summary-card"><span>Admins</span><strong>${counts.admins}</strong></div>
      <div class="summary-card"><span>Total Tasks</span><strong>${counts.tasks}</strong></div>
    </div>
  `;
}

function renderUsers(users) {
  adminUsers.className = "user-list";
  adminUsers.innerHTML = users.map((user) => `
    <article class="user-item">
      <h3>${escapeHtml(user.name)}</h3>
      <p>${escapeHtml(user.email)}</p>
      <span class="user-pill">${escapeHtml(user.role)}</span>
    </article>
  `).join("");
}

function populateTaskForm(taskId) {
  request(`/api/v1/tasks/${taskId}`, {
    method: "GET",
    headers: authHeaders(getToken())
  }).then((result) => {
    if (!result.ok) {
      showFlash(extractError(result.data), "error");
      return;
    }
    const current = result.data.data.task;
    document.getElementById("taskId").value = current.id;
    document.getElementById("taskTitle").value = current.title;
    document.getElementById("taskDescription").value = current.description || "";
    document.getElementById("taskStatus").value = current.status;
    document.getElementById("taskPriority").value = current.priority;
    document.getElementById("taskDueDate").value = current.due_date || "";
    window.scrollTo({ top: document.getElementById("taskForm").offsetTop - 20, behavior: "smooth" });
  });
}

async function deleteTask(taskId) {
  const token = getToken();
  if (!token) {
    showFlash("Please log in first.", "error");
    return;
  }

  const result = await request(`/api/v1/tasks/${taskId}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });

  if (!result.ok) {
    showFlash(extractError(result.data), "error");
    return;
  }

  showFlash(result.data.message, "success");
  loadTasks();
}

function clearTaskForm() {
  taskForm.reset();
  document.getElementById("taskId").value = "";
}

function logout() {
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(userKey);
  clearTaskForm();
  restoreSession();
  showFlash("Logged out successfully.", "success");
}

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  return { ok: response.ok, status: response.status, data };
}

function jsonHeaders() {
  return { "Content-Type": "application/json" };
}

function authHeaders(token) {
  return {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`
  };
}

function getToken() {
  return localStorage.getItem(tokenKey);
}

function getUser() {
  const raw = localStorage.getItem(userKey);
  return raw ? JSON.parse(raw) : null;
}

function extractError(payload) {
  if (payload.message) {
    return payload.message;
  }
  if (payload.messages) {
    return Object.values(payload.messages).flat().join(" ");
  }
  if (payload.error) {
    return payload.error;
  }
  return "Something went wrong.";
}

function showFlash(message, type) {
  flashMessage.textContent = message;
  flashMessage.className = `flash ${type}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#39;");
}

window.populateTaskForm = populateTaskForm;
window.deleteTask = deleteTask;
