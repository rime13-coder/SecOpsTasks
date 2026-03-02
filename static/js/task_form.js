let categoryDefaults = {};
let clientsCache = [];
let projectsCache = [];

async function loadCategories() {
    const cats = await API.getCategories();
    const sel = document.getElementById("category");
    sel.innerHTML = cats.map(c => `<option value="${c.category}">${c.category}</option>`).join("");
    cats.forEach(c => { categoryDefaults[c.category] = c.approval_mode; });
    onCategoryChange();
}

function onCategoryChange() {
    const cat = document.getElementById("category").value;
    const mode = categoryDefaults[cat] || "ask";
    document.querySelector(`input[name="approval_mode"][value="${mode}"]`).checked = true;
}

async function loadClients() {
    clientsCache = await API.manageListClients();
    const sel = document.getElementById("client_id");
    sel.innerHTML = '<option value="">Select a client...</option>' +
        clientsCache.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
}

async function onClientChange() {
    const clientId = document.getElementById("client_id").value;
    const projectSel = document.getElementById("project_id");
    const clientDescBox = document.getElementById("client-desc-box");

    if (!clientId) {
        projectSel.innerHTML = '<option value="">Select a project...</option>';
        clientDescBox.textContent = "";
        document.getElementById("project-desc-box").textContent = "";
        return;
    }

    // Show client description
    const client = clientsCache.find(c => c.id === parseInt(clientId));
    clientDescBox.textContent = client ? client.description : "";

    // Load projects for this client
    projectsCache = await API.manageListClientProjects(clientId);
    projectSel.innerHTML = '<option value="">Select a project...</option>' +
        projectsCache.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join("");

    // Clear project description
    document.getElementById("project-desc-box").textContent = "";
}

function onProjectChange() {
    const projectId = document.getElementById("project_id").value;
    const projectDescBox = document.getElementById("project-desc-box");

    if (!projectId) {
        projectDescBox.textContent = "";
        return;
    }

    const project = projectsCache.find(p => p.id === parseInt(projectId));
    projectDescBox.textContent = project ? project.description : "";
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        client_id: parseInt(form.client_id.value),
        project_id: parseInt(form.project_id.value),
        title: form.title.value.trim(),
        description: form.description.value.trim(),
        required_actions: form.required_actions.value.trim(),
        category: form.category.value,
        approval_mode: form.approval_mode.value,
        priority: form.priority.value,
    };
    const dueDate = form.due_date?.value;
    if (dueDate) data.due_date = dueDate;
    const maxRetries = parseInt(form.max_retries?.value) || 0;
    if (maxRetries > 0) data.max_retries = maxRetries;
    const recurrence = form.recurrence?.value;
    if (recurrence) data.recurrence = recurrence;
    const depsStr = form.depends_on?.value?.trim();
    if (depsStr) data.depends_on = depsStr.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));

    try {
        const task = await API.createTask(data);
        window.location.href = `task_detail.html?id=${task.id}`;
    } catch (err) {
        alert("Error creating task: " + err.message);
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadCategories();
    await loadClients();
    document.getElementById("category").addEventListener("change", onCategoryChange);
    document.getElementById("client_id").addEventListener("change", onClientChange);
    document.getElementById("project_id").addEventListener("change", onProjectChange);
    document.getElementById("task-form").addEventListener("submit", handleSubmit);
});
