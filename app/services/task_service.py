from __future__ import annotations
import json
from datetime import datetime, timezone
from app.database import get_db
from app.services.folder_service import ensure_output_folder


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


_TASK_SELECT = """
    SELECT t.id, t.title, t.description, t.required_actions,
           t.approval_mode, t.status, t.priority, t.category,
           t.due_date, t.depends_on, t.max_retries, t.retry_count,
           t.context, t.recurrence, t.source_template_id,
           t.progress, t.progress_total, t.progress_label,
           t.plan, t.summary, t.execution_log, t.output_folder,
           t.claimed_at, t.created_at, t.updated_at,
           COALESCE(c.name, t.client_name, '')          AS client_name,
           COALESCE(c.description, '')                   AS client_description,
           COALESCE(p.name, t.project_name, '')          AS project_name,
           COALESCE(p.description, '')                   AS project_description
    FROM tasks t
    LEFT JOIN clients  c ON c.id = t.client_id
    LEFT JOIN projects p ON p.id = t.project_id
"""


async def list_tasks(
    status: str | None = None,
    client: str | None = None,
    project: str | None = None,
    category: str | None = None,
    search: str | None = None,
) -> list[dict]:
    db = await get_db()
    clauses, params = [], []
    if status:
        clauses.append("t.status = ?")
        params.append(status)
    if client:
        clauses.append("c.name = ?")
        params.append(client)
    if project:
        clauses.append("p.name = ?")
        params.append(project)
    if category:
        clauses.append("t.category = ?")
        params.append(category)
    if search:
        clauses.append("(t.title LIKE ? OR t.description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    where = " AND ".join(clauses)
    sql = _TASK_SELECT + (f" WHERE {where}" if where else "") + " ORDER BY t.created_at DESC"
    rows = await db.execute(sql, params)
    return [_task_row(r) for r in await rows.fetchall()]


def _task_row(r) -> dict:
    d = dict(r)
    # Ensure JOIN columns are present even when NULLs
    d.setdefault("client_name", "")
    d.setdefault("client_description", "")
    d.setdefault("project_name", "")
    d.setdefault("project_description", "")
    # Parse JSON fields
    if isinstance(d.get("depends_on"), str):
        try:
            d["depends_on"] = json.loads(d["depends_on"])
        except (json.JSONDecodeError, TypeError):
            d["depends_on"] = []
    if isinstance(d.get("context"), str):
        try:
            d["context"] = json.loads(d["context"])
        except (json.JSONDecodeError, TypeError):
            d["context"] = {}
    return d


async def get_task(task_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute(_TASK_SELECT + " WHERE t.id = ?", (task_id,))
    r = await row.fetchone()
    return _task_row(r) if r else None


async def create_task(data: dict) -> dict:
    db = await get_db()
    now = _now()
    # Resolve names for the legacy text columns (still NOT NULL in schema)
    c_row = await db.execute("SELECT name, description FROM clients WHERE id = ?", (data["client_id"],))
    client = await c_row.fetchone()
    p_row = await db.execute("SELECT name, description FROM projects WHERE id = ?", (data["project_id"],))
    project = await p_row.fetchone()
    # Serialize JSON fields
    depends_on = json.dumps(data.get("depends_on", []))
    context = json.dumps(data.get("context", {}))
    row = await db.execute(
        """INSERT INTO tasks
           (client_id, project_id, client_name, project_name,
            title, description, required_actions,
            approval_mode, priority, category, due_date,
            depends_on, max_retries, context, recurrence, source_template_id,
            created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["client_id"], data["project_id"],
            client["name"] if client else "", project["name"] if project else "",
            data["title"],
            data.get("description", ""), data.get("required_actions", ""),
            data.get("approval_mode", "ask"), data.get("priority", "medium"),
            data.get("category", "general"), data.get("due_date"),
            depends_on, data.get("max_retries", 0), context,
            data.get("recurrence", ""), data.get("source_template_id"),
            now, now,
        ),
    )
    await db.commit()
    task = await get_task(row.lastrowid)
    await _fire_webhooks("task.created", task)
    return task


async def update_task(task_id: int, data: dict) -> dict | None:
    task = await get_task(task_id)
    if not task:
        return None
    old_status = task["status"]
    # Only allow updating actual task columns (not JOIN aliases)
    allowed = {
        "client_id", "project_id", "title", "description", "required_actions",
        "approval_mode", "priority", "category", "status", "plan", "summary",
        "execution_log", "output_folder", "claimed_at", "due_date",
        "depends_on", "max_retries", "retry_count", "context", "recurrence",
        "progress", "progress_total", "progress_label",
    }
    # Nullable columns that can be explicitly set to NULL
    nullable = {"claimed_at", "due_date", "source_template_id"}
    fields, params = [], []
    for key, val in data.items():
        if key not in allowed:
            continue
        if val is None and key not in nullable:
            continue
        # Serialize JSON fields for storage
        if key == "depends_on" and isinstance(val, list):
            val = json.dumps(val)
        if key == "context" and isinstance(val, dict):
            val = json.dumps(val)
        fields.append(f"{key} = ?")
        params.append(val)
    if not fields:
        return task
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(task_id)
    db = await get_db()
    await db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
    await db.commit()
    updated = await get_task(task_id)
    # Fire webhooks on status change
    new_status = updated["status"]
    if new_status != old_status:
        await _fire_webhooks("task.status_changed", updated)
        if new_status == "completed":
            await _fire_webhooks("task.completed", updated)
        elif new_status == "failed":
            await _fire_webhooks("task.failed", updated)
    # Check if plan needs approval
    if "plan" in data and data["plan"] and updated["status"] == "in_progress" and updated["approval_mode"] == "ask":
        await _fire_webhooks("task.needs_approval", updated)
    return updated


async def cancel_task(task_id: int) -> dict | None:
    return await update_task(task_id, {"status": "cancelled"})


async def destroy_task(task_id: int) -> bool:
    """Permanently delete a task from the database."""
    db = await get_db()
    task = await get_task(task_id)
    if not task:
        return False
    await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    await db.commit()
    return True


async def _dependencies_met(task: dict) -> bool:
    """Check if all dependency tasks are completed."""
    deps = task.get("depends_on", [])
    if not deps:
        return True
    db = await get_db()
    placeholders = ",".join("?" for _ in deps)
    row = await db.execute(
        f"SELECT COUNT(*) FROM tasks WHERE id IN ({placeholders}) AND status != 'completed'",
        deps,
    )
    count = (await row.fetchone())[0]
    return count == 0


async def claim_next_task() -> dict | None:
    db = await get_db()
    priority_order = "CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END"
    rows = await db.execute(
        _TASK_SELECT + f" WHERE t.status = 'pending' ORDER BY {priority_order}, t.created_at ASC"
    )
    candidates = [_task_row(r) for r in await rows.fetchall()]
    # Find first task with met dependencies
    task = None
    for candidate in candidates:
        if await _dependencies_met(candidate):
            task = candidate
            break
    if not task:
        return None
    now = _now()
    # Propagate context from completed dependencies
    merged_context = dict(task.get("context", {}))
    for dep_id in task.get("depends_on", []):
        dep = await get_task(dep_id)
        if dep and dep.get("context"):
            for k, v in dep["context"].items():
                if k not in merged_context:
                    merged_context[k] = v
    output_folder = ensure_output_folder(task["id"], task["client_name"], task["project_name"], task["title"])
    await db.execute(
        "UPDATE tasks SET status = 'in_progress', claimed_at = ?, output_folder = ?, context = ?, updated_at = ? WHERE id = ?",
        (now, output_folder, json.dumps(merged_context), now, task["id"]),
    )
    await db.commit()
    result = await get_task(task["id"])
    await _fire_webhooks("task.status_changed", result)
    return result


async def submit_plan(task_id: int, plan: str) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] != "in_progress":
        return None
    return await update_task(task_id, {"plan": plan})


async def approve_task(task_id: int) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] != "in_progress":
        return None
    return await update_task(task_id, {"status": "approved"})


async def reject_task(task_id: int) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] != "in_progress":
        return None
    return await update_task(task_id, {"status": "pending", "plan": "", "claimed_at": None, "output_folder": ""})


async def complete_task(task_id: int, summary: str, execution_log: str) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] not in ("in_progress", "approved"):
        return None
    result = await update_task(task_id, {"status": "completed", "summary": summary, "execution_log": execution_log})
    # Handle recurrence — create next instance
    if result and result.get("recurrence"):
        await _create_recurring_instance(result)
    return result


async def fail_task(task_id: int, error: str, execution_log: str) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] not in ("in_progress", "approved"):
        return None
    retry_count = task.get("retry_count", 0)
    max_retries = task.get("max_retries", 0)
    if retry_count < max_retries:
        # Auto-retry: increment count and requeue
        return await update_task(task_id, {
            "status": "pending",
            "retry_count": retry_count + 1,
            "plan": "",
            "claimed_at": None,
            "output_folder": "",
            "progress": 0,
            "progress_total": 0,
            "progress_label": "",
            "summary": f"Retry {retry_count + 1}/{max_retries}: {error}",
            "execution_log": execution_log,
        })
    return await update_task(task_id, {"status": "failed", "summary": error, "execution_log": execution_log})


async def update_progress(task_id: int, progress: int, progress_total: int, progress_label: str) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] not in ("in_progress", "approved"):
        return None
    return await update_task(task_id, {
        "progress": progress,
        "progress_total": progress_total,
        "progress_label": progress_label,
    })


async def _create_recurring_instance(completed_task: dict):
    """Create the next task instance for a recurring task."""
    from datetime import timedelta
    now_date = datetime.now(timezone.utc).date()
    # Calculate next due date based on recurrence
    recurrence = completed_task["recurrence"]
    due_date = None
    if recurrence == "daily":
        due_date = (now_date + timedelta(days=1)).isoformat()
    elif recurrence == "weekly":
        due_date = (now_date + timedelta(weeks=1)).isoformat()
    elif recurrence == "monthly":
        due_date = (now_date + timedelta(days=30)).isoformat()
    elif recurrence == "biweekly":
        due_date = (now_date + timedelta(weeks=2)).isoformat()

    db = await get_db()
    # Get client_id and project_id from the original task
    row = await db.execute("SELECT client_id, project_id FROM tasks WHERE id = ?", (completed_task["id"],))
    ids = await row.fetchone()
    if not ids or not ids["client_id"] or not ids["project_id"]:
        return

    new_data = {
        "client_id": ids["client_id"],
        "project_id": ids["project_id"],
        "title": completed_task["title"],
        "description": completed_task["description"],
        "required_actions": completed_task["required_actions"],
        "approval_mode": completed_task["approval_mode"],
        "priority": completed_task["priority"],
        "category": completed_task["category"],
        "due_date": due_date,
        "depends_on": [],
        "max_retries": completed_task.get("max_retries", 0),
        "context": completed_task.get("context", {}),
        "recurrence": recurrence,
        "source_template_id": completed_task.get("source_template_id"),
    }
    await create_task(new_data)


async def get_stats() -> dict:
    db = await get_db()
    row = await db.execute(
        """SELECT
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled
        FROM tasks"""
    )
    r = await row.fetchone()
    return {k: (r[k] or 0) for k in ("pending", "in_progress", "approved", "completed", "failed", "cancelled")}


async def get_categories() -> list[dict]:
    db = await get_db()
    rows = await db.execute("SELECT * FROM category_defaults ORDER BY category")
    return [dict(r) for r in await rows.fetchall()]


# ── Webhook firing ────────────────────────────────────────

async def _fire_webhooks(event: str, task: dict):
    """Fire matching webhooks in the background."""
    import asyncio
    try:
        db = await get_db()
        rows = await db.execute("SELECT * FROM webhooks WHERE active = 1")
        webhooks = [dict(r) for r in await rows.fetchall()]
    except Exception:
        return
    for wh in webhooks:
        try:
            events = json.loads(wh["events"]) if isinstance(wh["events"], str) else wh["events"]
        except (json.JSONDecodeError, TypeError):
            events = []
        if events and event not in events:
            continue
        asyncio.create_task(_deliver_webhook(wh, event, task))


async def _deliver_webhook(webhook: dict, event: str, task: dict):
    """Deliver a single webhook via async thread."""
    import asyncio
    import urllib.request
    import hmac
    import hashlib
    payload = json.dumps({"event": event, "task": _serialize_task(task)}).encode()
    try:
        req = urllib.request.Request(webhook["url"], data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Webhook-Event", event)
        if webhook.get("secret"):
            sig = hmac.new(webhook["secret"].encode(), payload, hashlib.sha256).hexdigest()
            req.add_header("X-Webhook-Signature", f"sha256={sig}")
        await asyncio.to_thread(urllib.request.urlopen, req, timeout=10)
    except Exception:
        pass  # Best-effort delivery


def _serialize_task(task: dict) -> dict:
    """Make task JSON-serializable (handle non-serializable types)."""
    out = {}
    for k, v in task.items():
        if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
            out[k] = v
        else:
            out[k] = str(v)
    return out
