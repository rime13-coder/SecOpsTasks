let editingId = null;

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function renderForm(client) {
    const isEdit = !!client;
    return `
        <div class="manage-form">
            <h3>${isEdit ? "Edit Client" : "Add Client"}</h3>
            <label>
                Name
                <input type="text" id="form-name" value="${isEdit ? escapeHtml(client.name) : ""}" required placeholder="Client name">
            </label>
            <label>
                Description
                <textarea id="form-desc" rows="3" placeholder="Client description...">${isEdit ? escapeHtml(client.description) : ""}</textarea>
            </label>
            <div class="form-actions">
                <button onclick="saveClient()">${isEdit ? "Update" : "Create"}</button>
                <button class="secondary outline" onclick="cancelForm()">Cancel</button>
            </div>
        </div>`;
}

function showAddForm() {
    editingId = null;
    document.getElementById("client-form-area").innerHTML = renderForm(null);
    document.getElementById("form-name").focus();
}

function showEditForm(client) {
    editingId = client.id;
    document.getElementById("client-form-area").innerHTML = renderForm(client);
    document.getElementById("form-name").focus();
}

function cancelForm() {
    editingId = null;
    document.getElementById("client-form-area").innerHTML = "";
}

async function saveClient() {
    const name = document.getElementById("form-name").value.trim();
    const description = document.getElementById("form-desc").value.trim();
    if (!name) { alert("Name is required"); return; }

    try {
        if (editingId) {
            await API.manageUpdateClient(editingId, { name, description });
        } else {
            await API.manageCreateClient({ name, description });
        }
        cancelForm();
        await loadClients();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function deleteClient(id, name) {
    if (!confirm(`Delete client "${name}"? This cannot be undone.`)) return;
    try {
        await API.manageDeleteClient(id);
        await loadClients();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

function renderCard(client) {
    return `
        <div class="manage-card">
            <h4>${escapeHtml(client.name)}</h4>
            <div class="card-desc">${escapeHtml(client.description) || '<em style="opacity:0.4">No description</em>'}</div>
            <div class="card-meta">Created ${new Date(client.created_at + "Z").toLocaleDateString()}</div>
            <div class="card-actions">
                <button class="outline" onclick='showEditForm(${JSON.stringify(client)})'>Edit</button>
                <button class="outline secondary" onclick="deleteClient(${client.id}, '${escapeHtml(client.name).replace(/'/g, "\\'")}')">Delete</button>
            </div>
        </div>`;
}

async function loadClients() {
    const clients = await API.manageListClients();
    const container = document.getElementById("client-list");
    if (clients.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No clients yet. Add one above.</p></div>';
    } else {
        container.innerHTML = clients.map(renderCard).join("");
    }
}

document.addEventListener("DOMContentLoaded", loadClients);
