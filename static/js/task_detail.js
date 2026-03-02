const taskId = new URLSearchParams(location.search).get("id");
let currentTask = null;

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadTask() {
    if (!taskId) { location.href = "/"; return; }
    const task = await API.getTask(taskId);
    currentTask = task;

    document.title = `#${task.id} ${task.title} — SecOps Tasks`;
    document.getElementById("task-title").textContent = `#${task.id} ${task.title}`;
    document.getElementById("task-status").textContent = task.status.replace("_", " ");
    document.getElementById("task-status").className = `badge badge-${task.status}`;
    document.getElementById("task-priority").textContent = task.priority;
    document.getElementById("task-priority").className = `badge badge-${task.priority}`;

    document.getElementById("detail-client").textContent = task.client_name;
    document.getElementById("detail-project").textContent = task.project_name;

    const clientDescRow = document.getElementById("client-desc-row");
    if (task.client_description) {
        clientDescRow.style.display = "block";
        document.getElementById("detail-client-desc").textContent = task.client_description;
    } else {
        clientDescRow.style.display = "none";
    }
    const projectDescRow = document.getElementById("project-desc-row");
    if (task.project_description) {
        projectDescRow.style.display = "block";
        document.getElementById("detail-project-desc").textContent = task.project_description;
    } else {
        projectDescRow.style.display = "none";
    }
    document.getElementById("detail-category").textContent = task.category;
    document.getElementById("detail-mode").textContent = task.approval_mode;
    document.getElementById("detail-due-date").textContent = task.due_date || "—";

    // New fields
    const deps = task.depends_on || [];
    document.getElementById("detail-depends-on").innerHTML = deps.length
        ? deps.map(id => `<a href="task_detail.html?id=${id}">#${id}</a>`).join(", ")
        : "—";
    document.getElementById("detail-retries").textContent =
        task.max_retries > 0 ? `${task.retry_count} / ${task.max_retries}` : "—";
    document.getElementById("detail-recurrence").textContent = task.recurrence || "—";

    document.getElementById("detail-created").textContent = new Date(task.created_at + "Z").toLocaleString();
    document.getElementById("detail-updated").textContent = new Date(task.updated_at + "Z").toLocaleString();
    document.getElementById("detail-claimed").textContent = task.claimed_at
        ? new Date(task.claimed_at + "Z").toLocaleString() : "—";
    document.getElementById("detail-folder").textContent = task.output_folder || "—";

    // Progress section
    const progressSection = document.getElementById("progress-section");
    if (task.progress_total > 0) {
        progressSection.style.display = "block";
        const pct = Math.round((task.progress / task.progress_total) * 100);
        document.getElementById("progress-fill").style.width = pct + "%";
        const label = task.progress_label || `${task.progress}/${task.progress_total}`;
        document.getElementById("progress-text").textContent = `${label} (${pct}%)`;
    } else {
        progressSection.style.display = "none";
    }

    // Context section
    const contextSection = document.getElementById("context-section");
    const ctx = task.context || {};
    if (Object.keys(ctx).length > 0) {
        contextSection.style.display = "block";
        document.getElementById("context-content").textContent = JSON.stringify(ctx, null, 2);
    } else {
        contextSection.style.display = "none";
    }

    document.getElementById("detail-description").textContent = task.description || "—";
    document.getElementById("detail-actions").textContent = task.required_actions || "—";

    // Plan section
    const planSection = document.getElementById("plan-section");
    if (task.plan) {
        planSection.style.display = "block";
        document.getElementById("plan-content").textContent = task.plan;
        const planActions = document.getElementById("plan-actions");
        planActions.style.display = (task.status === "in_progress" && task.approval_mode === "ask") ? "flex" : "none";
    } else {
        planSection.style.display = "none";
    }

    // Summary section
    const summarySection = document.getElementById("summary-section");
    if (task.summary) {
        summarySection.style.display = "block";
        document.getElementById("summary-content").textContent = task.summary;
    } else {
        summarySection.style.display = "none";
    }

    // Execution log
    const logSection = document.getElementById("log-section");
    if (task.execution_log) {
        logSection.style.display = "block";
        document.getElementById("log-content").textContent = task.execution_log;
    } else {
        logSection.style.display = "none";
    }

    // Action buttons
    const isDone = ["completed", "failed", "cancelled"].includes(task.status);
    const isActive = ["pending", "in_progress"].includes(task.status);
    document.getElementById("btn-cancel").style.display = isActive ? "inline-block" : "none";
    document.getElementById("btn-edit").style.display = isDone ? "inline-block" : "none";
    document.getElementById("btn-requeue").style.display = isDone ? "inline-block" : "none";
    document.getElementById("btn-delete").style.display = "inline-block";
}

async function approveTask() {
    await API.approveTask(taskId);
    loadTask();
}

async function rejectTask() {
    await API.rejectTask(taskId);
    loadTask();
}

async function cancelTask() {
    if (!confirm("Cancel this task?")) return;
    await API.deleteTask(taskId);
    loadTask();
}

async function destroyTask() {
    if (!confirm("Permanently delete this task? This cannot be undone.")) return;
    await API.destroyTask(taskId);
    location.href = "/";
}

function toggleEditForm() {
    const form = document.getElementById("edit-form");
    if (form.style.display === "none") {
        document.getElementById("edit-description").value = currentTask.description || "";
        document.getElementById("edit-actions").value = currentTask.required_actions || "";
        document.getElementById("edit-due-date").value = currentTask.due_date || "";
        document.getElementById("edit-max-retries").value = currentTask.max_retries || 0;
        document.getElementById("edit-recurrence").value = currentTask.recurrence || "";
        document.getElementById("edit-depends-on").value = (currentTask.depends_on || []).join(", ");
        document.getElementById("edit-notes").value = "";
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}

async function saveEdit() {
    const updates = {};
    const desc = document.getElementById("edit-description").value.trim();
    const actions = document.getElementById("edit-actions").value.trim();
    const notes = document.getElementById("edit-notes").value.trim();

    const dueDate = document.getElementById("edit-due-date").value || null;
    if (desc !== (currentTask.description || "")) updates.description = desc;
    if (actions !== (currentTask.required_actions || "")) updates.required_actions = actions;
    if (dueDate !== (currentTask.due_date || null)) updates.due_date = dueDate;

    const maxRetries = parseInt(document.getElementById("edit-max-retries").value) || 0;
    if (maxRetries !== (currentTask.max_retries || 0)) updates.max_retries = maxRetries;

    const recurrence = document.getElementById("edit-recurrence").value;
    if (recurrence !== (currentTask.recurrence || "")) updates.recurrence = recurrence;

    const depsStr = document.getElementById("edit-depends-on").value.trim();
    const newDeps = depsStr ? depsStr.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n)) : [];
    const oldDeps = currentTask.depends_on || [];
    if (JSON.stringify(newDeps) !== JSON.stringify(oldDeps)) updates.depends_on = newDeps;

    if (notes) {
        const existing = currentTask.summary || "";
        updates.summary = existing ? existing + "\n\n--- Notes ---\n" + notes : notes;
    }

    if (Object.keys(updates).length === 0) {
        document.getElementById("edit-form").style.display = "none";
        return;
    }

    try {
        await API.updateTask(taskId, updates);
        document.getElementById("edit-form").style.display = "none";
        await loadTask();
    } catch (err) {
        alert("Error saving: " + err.message);
    }
}

async function requeueTask() {
    if (!confirm("Requeue this task for execution? Status will be set back to pending.")) return;
    try {
        await API.updateTask(taskId, {
            status: "pending",
            plan: "",
            execution_log: "",
            claimed_at: null
        });
        await loadTask();
    } catch (err) {
        alert("Error requeuing: " + err.message);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadTask();
    setInterval(loadTask, 10000);
});
