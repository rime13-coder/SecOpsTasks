let clientsCache = [];
let projectsCache = [];

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

async function loadClients() {
    clientsCache = await API.manageListClients();
    const sel = document.getElementById("form-client");
    sel.innerHTML = '<option value="">Select...</option>' +
        clientsCache.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
}

async function onClientChange() {
    const clientId = document.getElementById("form-client").value;
    const projectSel = document.getElementById("form-project");
    if (!clientId) {
        projectSel.innerHTML = '<option value="">Select...</option>';
        return;
    }
    projectsCache = await API.manageListClientProjects(clientId);
    projectSel.innerHTML = '<option value="">Select...</option>' +
        projectsCache.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");
}

async function loadTemplates() {
    const templates = await API.getTemplates();
    const grid = document.getElementById("templates-grid");
    if (templates.length === 0) {
        grid.innerHTML = '<div class="empty-state"><p>No templates yet. Create one to get started.</p></div>';
        return;
    }
    grid.innerHTML = templates.map(t => `
        <div class="manage-card">
            <h4>${escapeHtml(t.name)}</h4>
            <div class="card-desc">${escapeHtml(t.title)}</div>
            <div class="card-meta">
                ${escapeHtml(t.client_name || "—")} / ${escapeHtml(t.project_name || "—")}
                &middot; ${t.category} &middot; ${t.priority}
                ${t.recurrence ? `&middot; <strong>${t.recurrence}</strong>` : ""}
                ${t.active ? "" : " &middot; <em>inactive</em>"}
            </div>
            <div class="card-actions">
                <button class="outline" onclick="createFromTemplate(${t.id})">Create Task</button>
                <button class="outline secondary" onclick="editTemplate(${t.id})">Edit</button>
                <button class="outline" style="--pico-color:var(--failed)" onclick="deleteTemplate(${t.id})">Delete</button>
            </div>
        </div>
    `).join("");
}

function showAddForm() {
    document.getElementById("form-id").value = "";
    document.getElementById("form-title").textContent = "New Template";
    document.getElementById("form-name").value = "";
    document.getElementById("form-client").value = "";
    document.getElementById("form-project").innerHTML = '<option value="">Select...</option>';
    document.getElementById("form-title-field").value = "";
    document.getElementById("form-category").value = "general";
    document.getElementById("form-priority").value = "medium";
    document.getElementById("form-approval").value = "ask";
    document.getElementById("form-offset").value = "";
    document.getElementById("form-retries").value = "0";
    document.getElementById("form-recurrence").value = "";
    document.getElementById("form-description").value = "";
    document.getElementById("form-actions").value = "";
    document.getElementById("template-form").style.display = "block";
}

async function editTemplate(id) {
    const t = await API.getTemplate(id);
    document.getElementById("form-id").value = t.id;
    document.getElementById("form-title").textContent = "Edit Template";
    document.getElementById("form-name").value = t.name;
    document.getElementById("form-client").value = t.client_id || "";
    if (t.client_id) {
        await onClientChange();
        document.getElementById("form-project").value = t.project_id || "";
    }
    document.getElementById("form-title-field").value = t.title;
    document.getElementById("form-category").value = t.category;
    document.getElementById("form-priority").value = t.priority;
    document.getElementById("form-approval").value = t.approval_mode;
    document.getElementById("form-offset").value = t.due_date_offset ?? "";
    document.getElementById("form-retries").value = t.max_retries;
    document.getElementById("form-recurrence").value = t.recurrence;
    document.getElementById("form-description").value = t.description;
    document.getElementById("form-actions").value = t.required_actions;
    document.getElementById("template-form").style.display = "block";
}

function hideForm() {
    document.getElementById("template-form").style.display = "none";
}

async function saveTemplate() {
    const data = {
        name: document.getElementById("form-name").value.trim(),
        client_id: parseInt(document.getElementById("form-client").value) || null,
        project_id: parseInt(document.getElementById("form-project").value) || null,
        title: document.getElementById("form-title-field").value.trim(),
        category: document.getElementById("form-category").value,
        priority: document.getElementById("form-priority").value,
        approval_mode: document.getElementById("form-approval").value,
        max_retries: parseInt(document.getElementById("form-retries").value) || 0,
        recurrence: document.getElementById("form-recurrence").value,
        description: document.getElementById("form-description").value.trim(),
        required_actions: document.getElementById("form-actions").value.trim(),
    };
    const offset = document.getElementById("form-offset").value;
    if (offset !== "") data.due_date_offset = parseInt(offset);

    try {
        const id = document.getElementById("form-id").value;
        if (id) {
            await API.updateTemplate(parseInt(id), data);
        } else {
            await API.createTemplate(data);
        }
        hideForm();
        await loadTemplates();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function createFromTemplate(id) {
    try {
        const task = await API.createTaskFromTemplate(id);
        window.location.href = `task_detail.html?id=${task.id}`;
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function deleteTemplate(id) {
    if (!confirm("Delete this template?")) return;
    await API.deleteTemplate(id);
    await loadTemplates();
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadClients();
    document.getElementById("form-client").addEventListener("change", onClientChange);
    await loadTemplates();
});
