let refreshTimer;

async function loadStats() {
    const stats = await API.getStats();
    document.getElementById("stats-row").innerHTML = [
        { label: "Pending", value: stats.pending, cls: "pending" },
        { label: "In Progress", value: stats.in_progress, cls: "in_progress" },
        { label: "Approved", value: stats.approved, cls: "approved" },
        { label: "Completed", value: stats.completed, cls: "completed" },
        { label: "Failed", value: stats.failed, cls: "failed" },
    ].map(s => `
        <div class="stat-card">
            <div class="stat-value" style="color: var(--${s.cls})">${s.value}</div>
            <div class="stat-label">${s.label}</div>
        </div>
    `).join("");
}

async function loadFilters() {
    const clients = await API.getClients();
    const sel = document.getElementById("filter-client");
    sel.innerHTML = '<option value="">All Clients</option>' +
        clients.map(c => `<option value="${c}">${c}</option>`).join("");
}

function renderTaskCard(task) {
    const needsApproval = task.status === "in_progress" && task.approval_mode === "ask" && task.plan;
    let actions = "";
    if (needsApproval) {
        actions = `
            <div class="task-card-actions" onclick="event.stopPropagation()">
                <button class="outline" onclick="approveTask(${task.id})" style="--pico-color: var(--completed)">Approve</button>
                <button class="outline secondary" onclick="rejectTask(${task.id})">Reject</button>
            </div>`;
    }
    return `
        <div class="task-card" onclick="location.href='task_detail.html?id=${task.id}'">
            <div class="task-card-header">
                <h4>#${task.id} ${escapeHtml(task.title)}</h4>
                <div class="task-card-badges">
                    <span class="badge badge-${task.priority}">${task.priority}</span>
                    <span class="badge badge-${task.status}">${task.status.replace("_", " ")}</span>
                </div>
            </div>
            <div class="task-card-meta">
                ${escapeHtml(task.client_name)} / ${escapeHtml(task.project_name)}
                &middot; ${task.category}
                &middot; ${task.approval_mode}
                &middot; ${new Date(task.created_at + "Z").toLocaleString()}
            </div>
            ${needsApproval ? `<div style="margin-top:0.5rem;font-size:0.85rem;color:var(--pico-primary)">Plan submitted — awaiting approval</div>` : ""}
            ${actions}
        </div>`;
}

async function loadTasks() {
    const params = {};
    const status = document.getElementById("filter-status")?.value;
    const client = document.getElementById("filter-client")?.value;
    const category = document.getElementById("filter-category")?.value;
    if (status) params.status = status;
    if (client) params.client = client;
    if (category) params.category = category;

    const tasks = await API.getTasks(params);
    const container = document.getElementById("task-list");
    if (tasks.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No tasks found</p></div>';
    } else {
        container.innerHTML = tasks.map(renderTaskCard).join("");
    }
}

async function approveTask(id) {
    await API.approveTask(id);
    refresh();
}

async function rejectTask(id) {
    await API.rejectTask(id);
    refresh();
}

async function refresh() {
    await Promise.all([loadStats(), loadTasks()]);
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadFilters();
    await refresh();

    document.getElementById("filter-status")?.addEventListener("change", loadTasks);
    document.getElementById("filter-client")?.addEventListener("change", loadTasks);
    document.getElementById("filter-category")?.addEventListener("change", loadTasks);

    refreshTimer = setInterval(refresh, 10000);
});
