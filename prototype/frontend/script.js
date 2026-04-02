const metricsEl = document.getElementById("metrics");
const seuListEl = document.getElementById("seuList");
const taskTableEl = document.getElementById("taskTable");
const apiBaseInput = document.getElementById("apiBase");
const taskForm = document.getElementById("taskForm");
const scenarioButtons = document.querySelectorAll("[data-scenario]");

const statusClass = (value) => {
  const normalized = (value || "").toLowerCase();
  if (normalized === "pending" || normalized === "deferred") return "status-pending";
  if (normalized === "executing") return "status-executing";
  if (normalized === "completed") return "status-completed";
  return "status-failed";
};

const apiBase = () => apiBaseInput.value.replace(/\/$/, "");

const renderMetrics = (metrics) => {
  const cards = [
    ["Tasks received", metrics.total_tasks_received],
    ["SEUs executed", metrics.total_seus_executed],
    ["Executions saved", metrics.executions_saved],
    ["Completed tasks", metrics.total_completed_tasks],
    ["Pending SEUs", metrics.active_pending_seus],
    ["Dedup multiplier", `${metrics.dedup_multiplier}x`],
  ];
  metricsEl.innerHTML = cards.map(([label, value]) => `
    <article class="metric-card">
      <span>${label}</span>
      <strong>${value}</strong>
    </article>`).join("");
};

const renderSeus = (seus) => {
  if (!seus.length) {
    seuListEl.innerHTML = '<p class="muted">No shared execution units yet. Launch a scenario to see Temporal Admission and collapse behavior.</p>';
    return;
  }
  const now = Date.now() / 1000;
  seuListEl.innerHTML = seus.map((seu) => {
    const windowTotal = seu.admission_window_ms / 1000;
    const remaining = Math.max(0, seu.admission_deadline - now);
    const progress = windowTotal > 0 ? Math.max(0, Math.min(100, ((windowTotal - remaining) / windowTotal) * 100)) : 100;
    return `
      <article class="seu-card">
        <div class="seu-header">
          <div><strong>${seu.seu_id}</strong><p class="muted">${seu.task_type}</p></div>
          <span class="status-tag ${statusClass(seu.status)}">${seu.status}</span>
        </div>
        <div class="timer-bar"><div class="timer-fill" style="width:${progress}%"></div></div>
        <p class="subscriber-list">Subscribers: ${seu.subscriber_agent_ids.join(", ") || "None"} | Matches: ${seu.match_reasons.join(", ")}</p>
        <p class="muted">${seu.canonical}</p>
      </article>`;
  }).join("");
};

const renderTasks = (tasks) => {
  if (!tasks.length) {
    taskTableEl.innerHTML = '<tr><td colspan="6" class="muted">No tasks submitted yet.</td></tr>';
    return;
  }
  taskTableEl.innerHTML = tasks.map((task) => `
    <tr>
      <td>${task.task_id}</td>
      <td>${task.agent_id}</td>
      <td>${task.task_type}</td>
      <td><span class="status-tag ${statusClass(task.status)}">${task.status}</span></td>
      <td>${task.seu_id || "-"}</td>
      <td>${task.match_type || "-"}</td>
    </tr>`).join("");
};

const refreshState = async () => {
  const response = await fetch(`${apiBase()}/state`);
  const state = await response.json();
  renderMetrics(state.metrics);
  renderSeus(state.seus);
  renderTasks(state.tasks);
};

const submitScenario = async (name) => {
  await fetch(`${apiBase()}/scenarios/${name}`, { method: "POST" });
  await refreshState();
};

const submitTask = async (event) => {
  event.preventDefault();
  const form = new FormData(taskForm);
  await fetch(`${apiBase()}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.fromEntries(form.entries())),
  });
  await refreshState();
};

scenarioButtons.forEach((button) => {
  button.addEventListener("click", () => submitScenario(button.dataset.scenario));
});

taskForm.addEventListener("submit", submitTask);
apiBaseInput.addEventListener("change", refreshState);

refreshState().catch((error) => {
  metricsEl.innerHTML = `<article class="metric-card"><span>Connection</span><strong>Unavailable</strong><p class="muted">${error.message}</p></article>`;
});

setInterval(() => {
  refreshState().catch(() => undefined);
}, 1000);
