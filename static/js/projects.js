let editingId = null;
let clientsCache = [];

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadClientFilter() {
    clientsCache = await API.manageListClients();
    const sel = document.getElementById("filter-client");
    sel.innerHTML = '<option value="">All Clients</option>' +
        clientsCache.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join("");
}

function clientOptions(selectedId) {
    return clientsCache.map(c =>
        `<option value="${c.id}" ${c.id === selectedId ? "selected" : ""}>${escapeHtml(c.name)}</option>`
    ).join("");
}

function renderForm(project) {
    const isEdit = !!project;
    return `
        <div class="manage-form">
            <h3>${isEdit ? "Edit Project" : "Add Project"}</h3>
            ${isEdit ? "" : `
            <label>
                Client
                <select id="form-client">${clientOptions(null)}</select>
            </label>`}
            <label>
                Name
                <input type="text" id="form-name" value="${isEdit ? escapeHtml(project.name) : ""}" required placeholder="Project name">
            </label>
            <label>
                Description
                <textarea id="form-desc" rows="3" placeholder="Project description...">${isEdit ? escapeHtml(project.description) : ""}</textarea>
            </label>
            <div class="form-actions">
                <button onclick="saveProject()">${isEdit ? "Update" : "Create"}</button>
                <button class="secondary outline" onclick="cancelForm()">Cancel</button>
            </div>
        </div>`;
}

function showAddForm() {
    if (clientsCache.length === 0) {
        alert("Please create a client first.");
        return;
    }
    editingId = null;
    document.getElementById("project-form-area").innerHTML = renderForm(null);
    document.getElementById("form-name").focus();
}

function showEditForm(project) {
    editingId = project.id;
    document.getElementById("project-form-area").innerHTML = renderForm(project);
    document.getElementById("form-name").focus();
}

function cancelForm() {
    editingId = null;
    document.getElementById("project-form-area").innerHTML = "";
}

async function saveProject() {
    const name = document.getElementById("form-name").value.trim();
    const description = document.getElementById("form-desc").value.trim();
    if (!name) { alert("Name is required"); return; }

    try {
        if (editingId) {
            await API.manageUpdateProject(editingId, { name, description });
        } else {
            const clientId = parseInt(document.getElementById("form-client").value);
            await API.manageCreateProject({ client_id: clientId, name, description });
        }
        cancelForm();
        await loadProjects();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function deleteProject(id, name) {
    if (!confirm(`Delete project "${name}"? This cannot be undone.`)) return;
    try {
        await API.manageDeleteProject(id);
        await loadProjects();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

function renderCard(project) {
    return `
        <div class="manage-card">
            <h4>${escapeHtml(project.name)}</h4>
            <div class="card-meta">${escapeHtml(project.client_name)}</div>
            <div class="card-desc">${escapeHtml(project.description) || '<em style="opacity:0.4">No description</em>'}</div>
            <div class="card-actions">
                <button class="outline" onclick='showEditForm(${JSON.stringify(project)})'>Edit</button>
                <button class="outline secondary" onclick="deleteProject(${project.id}, '${escapeHtml(project.name).replace(/'/g, "\\'")}')">Delete</button>
            </div>
        </div>`;
}

async function loadProjects() {
    const clientId = document.getElementById("filter-client").value || undefined;
    const projects = await API.manageListProjects(clientId);
    const container = document.getElementById("project-list");
    if (projects.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No projects found. Add one above.</p></div>';
    } else {
        container.innerHTML = projects.map(renderCard).join("");
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    await loadClientFilter();
    await loadProjects();
    document.getElementById("filter-client").addEventListener("change", loadProjects);
});
