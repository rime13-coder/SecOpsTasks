function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

async function loadWebhooks() {
    const webhooks = await API.getWebhooks();
    const grid = document.getElementById("webhooks-grid");
    if (webhooks.length === 0) {
        grid.innerHTML = '<div class="empty-state"><p>No webhooks configured.</p></div>';
        return;
    }
    grid.innerHTML = webhooks.map(w => {
        const events = w.events && w.events.length ? w.events.join(", ") : "all events";
        return `
            <div class="manage-card">
                <h4>${escapeHtml(w.url)}</h4>
                <div class="card-desc">Events: ${escapeHtml(events)}</div>
                <div class="card-meta">
                    ${w.active ? "Active" : "Inactive"}
                    ${w.secret ? " &middot; Signed" : ""}
                </div>
                <div class="card-actions">
                    <button class="outline secondary" onclick="toggleActive(${w.id}, ${w.active})">${w.active ? "Disable" : "Enable"}</button>
                    <button class="outline secondary" onclick="editWebhook(${w.id})">Edit</button>
                    <button class="outline" style="--pico-color:var(--failed)" onclick="deleteWebhook(${w.id})">Delete</button>
                </div>
            </div>`;
    }).join("");
}

function showAddForm() {
    document.getElementById("wh-form-id").value = "";
    document.getElementById("wh-form-title").textContent = "New Webhook";
    document.getElementById("wh-url").value = "";
    document.getElementById("wh-secret").value = "";
    document.getElementById("wh-events").value = "";
    document.getElementById("webhook-form").style.display = "block";
}

async function editWebhook(id) {
    const w = await API.getWebhook(id);
    document.getElementById("wh-form-id").value = w.id;
    document.getElementById("wh-form-title").textContent = "Edit Webhook";
    document.getElementById("wh-url").value = w.url;
    document.getElementById("wh-secret").value = w.secret;
    document.getElementById("wh-events").value = (w.events || []).join(", ");
    document.getElementById("webhook-form").style.display = "block";
}

function hideForm() {
    document.getElementById("webhook-form").style.display = "none";
}

async function saveWebhook() {
    const eventsStr = document.getElementById("wh-events").value.trim();
    const data = {
        url: document.getElementById("wh-url").value.trim(),
        secret: document.getElementById("wh-secret").value.trim(),
        events: eventsStr ? eventsStr.split(",").map(s => s.trim()).filter(Boolean) : [],
    };
    try {
        const id = document.getElementById("wh-form-id").value;
        if (id) {
            await API.updateWebhook(parseInt(id), data);
        } else {
            await API.createWebhook(data);
        }
        hideForm();
        await loadWebhooks();
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function toggleActive(id, current) {
    await API.updateWebhook(id, { active: !current });
    await loadWebhooks();
}

async function deleteWebhook(id) {
    if (!confirm("Delete this webhook?")) return;
    await API.deleteWebhook(id);
    await loadWebhooks();
}

document.addEventListener("DOMContentLoaded", () => {
    loadWebhooks();
});
