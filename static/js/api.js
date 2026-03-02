const API = {
    async request(method, path, body) {
        const opts = { method, headers: { "Content-Type": "application/json" } };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(path, opts);
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || res.statusText);
        }
        return res.json();
    },

    getTasks(params = {}) {
        const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
        return this.request("GET", `/api/tasks${qs ? "?" + qs : ""}`);
    },

    getTask(id) { return this.request("GET", `/api/tasks/${id}`); },
    createTask(data) { return this.request("POST", "/api/tasks", data); },
    updateTask(id, data) { return this.request("PUT", `/api/tasks/${id}`, data); },
    deleteTask(id) { return this.request("DELETE", `/api/tasks/${id}`); },

    getStats() { return this.request("GET", "/api/tasks/stats"); },
    getClients() { return this.request("GET", "/api/clients"); },
    getProjects(client) { return this.request("GET", `/api/clients/${encodeURIComponent(client)}/projects`); },
    getCategories() { return this.request("GET", "/api/categories"); },

    approveTask(id) { return this.request("POST", `/api/execution/${id}/approve`); },
    rejectTask(id) { return this.request("POST", `/api/execution/${id}/reject`); },
    destroyTask(id) { return this.request("POST", `/api/tasks/${id}/destroy`); },

    // Management API
    manageListClients() { return this.request("GET", "/api/manage/clients"); },
    manageGetClient(id) { return this.request("GET", `/api/manage/clients/${id}`); },
    manageCreateClient(data) { return this.request("POST", "/api/manage/clients", data); },
    manageUpdateClient(id, data) { return this.request("PUT", `/api/manage/clients/${id}`, data); },
    manageDeleteClient(id) { return this.request("DELETE", `/api/manage/clients/${id}`); },
    manageListClientProjects(id) { return this.request("GET", `/api/manage/clients/${id}/projects`); },

    manageListProjects(clientId) {
        const qs = clientId ? `?client_id=${clientId}` : "";
        return this.request("GET", `/api/manage/projects${qs}`);
    },
    manageGetProject(id) { return this.request("GET", `/api/manage/projects/${id}`); },
    manageCreateProject(data) { return this.request("POST", "/api/manage/projects", data); },
    manageUpdateProject(id, data) { return this.request("PUT", `/api/manage/projects/${id}`, data); },
    manageDeleteProject(id) { return this.request("DELETE", `/api/manage/projects/${id}`); },

    // Templates API
    getTemplates() { return this.request("GET", "/api/templates"); },
    getTemplate(id) { return this.request("GET", `/api/templates/${id}`); },
    createTemplate(data) { return this.request("POST", "/api/templates", data); },
    updateTemplate(id, data) { return this.request("PUT", `/api/templates/${id}`, data); },
    deleteTemplate(id) { return this.request("DELETE", `/api/templates/${id}`); },
    createTaskFromTemplate(id) { return this.request("POST", `/api/templates/${id}/create-task`); },

    // Webhooks API
    getWebhooks() { return this.request("GET", "/api/webhooks"); },
    getWebhook(id) { return this.request("GET", `/api/webhooks/${id}`); },
    createWebhook(data) { return this.request("POST", "/api/webhooks", data); },
    updateWebhook(id, data) { return this.request("PUT", `/api/webhooks/${id}`, data); },
    deleteWebhook(id) { return this.request("DELETE", `/api/webhooks/${id}`); },
};
