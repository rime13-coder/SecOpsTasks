let refreshTimer;
let searchDebounce = null;

const KANBAN_COLUMNS = [
    { key: "pending",     label: "Pending",     statusList: ["pending"],     color: "var(--pending)" },
    { key: "in_progress", label: "In Progress", statusList: ["in_progress"], color: "var(--in-progress)" },
    { key: "approved",    label: "Approved",    statusList: ["approved"],    color: "var(--approved)" },
    { key: "completed",   label: "Completed",   statusList: ["completed"],   color: "var(--completed)" },
    { key: "closed",      label: "Closed",      statusList: ["failed", "cancelled"], color: "var(--failed)" },
];

function initBoard() {
    const board = document.getElementById("kanban-board");
    board.innerHTML = KANBAN_COLUMNS.map(col => `
        <div class="kanban-column" data-column="${col.key}">
            <div class="kanban-column-header" style="border-top-color: ${col.color}">
                <span class="kanban-column-title">${col.label}</span>
                <span class="kanban-column-count" data-count="${col.key}">0</span>
            </div>
            <div class="kanban-column-body" data-body="${col.key}"></div>
        </div>
    `).join("");
}

function formatDueDate(dateStr) {
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const [y, m, d] = dateStr.split("-").map(Number);
    return `Due ${months[m - 1]} ${d}`;
}

function isOverdue(task) {
    if (!task.due_date) return false;
    const terminal = ["completed", "failed", "cancelled"];
    if (terminal.includes(task.status)) return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(task.due_date + "T00:00:00");
    return due < today;
}

function renderTaskCard(task) {
    const needsApproval = task.status === "in_progress" && task.approval_mode === "ask" && task.plan;
    const isClosedTerminal = task.status === "failed" || task.status === "cancelled";

    let actions = "";
    if (needsApproval) {
        actions = `
            <div class="kanban-card-actions" onclick="event.stopPropagation()">
                <button class="outline" onclick="approveTask(${task.id})" style="--pico-color: var(--completed)">Approve</button>
                <button class="outline secondary" onclick="rejectTask(${task.id})">Reject</button>
            </div>`;
    }

    const closedBadge = isClosedTerminal
        ? `<span class="badge badge-${task.status}">${task.status === "failed" ? "failed" : "cancelled"}</span>`
        : "";

    const dueDateHtml = task.due_date
        ? `<div class="kanban-card-due${isOverdue(task) ? " overdue" : ""}">${formatDueDate(task.due_date)}</div>`
        : "";

    // Progress bar
    let progressHtml = "";
    if (task.progress_total > 0) {
        const pct = Math.round((task.progress / task.progress_total) * 100);
        const label = task.progress_label || `${task.progress}/${task.progress_total}`;
        progressHtml = `
            <div class="kanban-card-progress">
                <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
                <span class="progress-text">${escapeHtml(label)}</span>
            </div>`;
    }

    // Indicators: deps, retries, recurrence
    const indicators = [];
    if (task.depends_on && task.depends_on.length > 0)
        indicators.push(`<span class="card-indicator" title="Depends on ${task.depends_on.length} task(s)">&#x1f517;${task.depends_on.length}</span>`);
    if (task.max_retries > 0)
        indicators.push(`<span class="card-indicator" title="Retries: ${task.retry_count}/${task.max_retries}">&#x21bb;${task.retry_count}/${task.max_retries}</span>`);
    if (task.recurrence)
        indicators.push(`<span class="card-indicator" title="Recurring: ${task.recurrence}">&#x1f501;${task.recurrence}</span>`);
    const indicatorHtml = indicators.length ? `<div class="kanban-card-indicators">${indicators.join(" ")}</div>` : "";

    return `
        <div class="kanban-card" onclick="location.href='task_detail.html?id=${task.id}'">
            <div class="kanban-card-header">
                <span class="kanban-card-title">#${task.id} ${escapeHtml(task.title)}</span>
                <span class="badge badge-${task.priority}">${task.priority}</span>
            </div>
            <div class="kanban-card-meta">
                ${escapeHtml(task.client_name)} / ${escapeHtml(task.project_name)}
                &middot; ${task.category}
            </div>
            ${dueDateHtml}
            ${indicatorHtml}
            ${progressHtml}
            ${closedBadge ? `<div class="kanban-card-closed">${closedBadge}</div>` : ""}
            ${needsApproval ? `<div class="kanban-card-approval">Plan submitted — awaiting approval</div>` : ""}
            ${actions}
        </div>`;
}

function saveScrollPositions() {
    const positions = {};
    for (const col of KANBAN_COLUMNS) {
        const body = document.querySelector(`[data-body="${col.key}"]`);
        if (body) positions[col.key] = body.scrollTop;
    }
    return positions;
}

function restoreScrollPositions(positions) {
    for (const col of KANBAN_COLUMNS) {
        const body = document.querySelector(`[data-body="${col.key}"]`);
        if (body && positions[col.key] !== undefined) {
            body.scrollTop = positions[col.key];
        }
    }
}

async function loadFilters() {
    const clients = await API.getClients();
    const sel = document.getElementById("filter-client");
    sel.innerHTML = '<option value="">All Clients</option>' +
        clients.map(c => `<option value="${c}">${c}</option>`).join("");
}

async function loadTasks() {
    const scrollPos = saveScrollPositions();

    const params = {};
    const client = document.getElementById("filter-client")?.value;
    const category = document.getElementById("filter-category")?.value;
    const search = document.getElementById("filter-search")?.value?.trim();
    if (client) params.client = client;
    if (category) params.category = category;
    if (search) params.search = search;

    const tasks = await API.getTasks(params);

    // Group tasks by column
    const grouped = {};
    for (const col of KANBAN_COLUMNS) {
        grouped[col.key] = [];
    }

    for (const task of tasks) {
        for (const col of KANBAN_COLUMNS) {
            if (col.statusList.includes(task.status)) {
                grouped[col.key].push(task);
                break;
            }
        }
    }

    // Render cards into columns and update counts
    for (const col of KANBAN_COLUMNS) {
        const body = document.querySelector(`[data-body="${col.key}"]`);
        const count = document.querySelector(`[data-count="${col.key}"]`);
        const cards = grouped[col.key];

        if (count) count.textContent = cards.length;

        if (body) {
            if (cards.length === 0) {
                body.innerHTML = '<div class="kanban-empty">No tasks</div>';
            } else {
                body.innerHTML = cards.map(renderTaskCard).join("");
            }
        }
    }

    restoreScrollPositions(scrollPos);

    // Update document title with pending count
    const pendingCount = (grouped["pending"] || []).length;
    document.title = pendingCount > 0 ? `(${pendingCount}) SecOps Tasks` : "SecOps Tasks";
}

async function approveTask(id) {
    await API.approveTask(id);
    await loadTasks();
}

async function rejectTask(id) {
    await API.rejectTask(id);
    await loadTasks();
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", async () => {
    initBoard();
    await loadFilters();
    await loadTasks();

    document.getElementById("filter-client")?.addEventListener("change", loadTasks);
    document.getElementById("filter-category")?.addEventListener("change", loadTasks);

    document.getElementById("filter-search")?.addEventListener("input", () => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(loadTasks, 300);
    });

    refreshTimer = setInterval(loadTasks, 10000);
});
