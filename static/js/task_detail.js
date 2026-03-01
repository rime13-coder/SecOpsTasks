const taskId = new URLSearchParams(location.search).get("id");

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadTask() {
    if (!taskId) { location.href = "/"; return; }
    const task = await API.getTask(taskId);
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
    document.getElementById("detail-created").textContent = new Date(task.created_at + "Z").toLocaleString();
    document.getElementById("detail-updated").textContent = new Date(task.updated_at + "Z").toLocaleString();
    document.getElementById("detail-claimed").textContent = task.claimed_at
        ? new Date(task.claimed_at + "Z").toLocaleString() : "—";
    document.getElementById("detail-folder").textContent = task.output_folder || "—";

    document.getElementById("detail-description").textContent = task.description || "—";
    document.getElementById("detail-actions").textContent = task.required_actions || "—";

    // Plan section
    const planSection = document.getElementById("plan-section");
    if (task.plan) {
        planSection.style.display = "block";
        document.getElementById("plan-content").textContent = task.plan;
        const planActions = document.getElementById("plan-actions");
        if (task.status === "in_progress" && task.approval_mode === "ask") {
            planActions.style.display = "flex";
        } else {
            planActions.style.display = "none";
        }
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

    // Cancel button
    const cancelBtn = document.getElementById("btn-cancel");
    if (["pending", "in_progress"].includes(task.status)) {
        cancelBtn.style.display = "inline-block";
    } else {
        cancelBtn.style.display = "none";
    }
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

document.addEventListener("DOMContentLoaded", () => {
    loadTask();
    setInterval(loadTask, 10000);
});
