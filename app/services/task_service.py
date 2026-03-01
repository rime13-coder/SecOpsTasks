from __future__ import annotations
from datetime import datetime, timezone
from app.database import get_db
from app.services.folder_service import ensure_output_folder


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


_TASK_SELECT = """
    SELECT t.id, t.title, t.description, t.required_actions,
           t.approval_mode, t.status, t.priority, t.category,
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
    row = await db.execute(
        """INSERT INTO tasks
           (client_id, project_id, client_name, project_name,
            title, description, required_actions,
            approval_mode, priority, category, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["client_id"], data["project_id"],
            client["name"] if client else "", project["name"] if project else "",
            data["title"],
            data.get("description", ""), data.get("required_actions", ""),
            data.get("approval_mode", "ask"), data.get("priority", "medium"),
            data.get("category", "general"), now, now,
        ),
    )
    await db.commit()
    return await get_task(row.lastrowid)


async def update_task(task_id: int, data: dict) -> dict | None:
    task = await get_task(task_id)
    if not task:
        return None
    # Only allow updating actual task columns (not JOIN aliases)
    allowed = {
        "client_id", "project_id", "title", "description", "required_actions",
        "approval_mode", "priority", "category", "status", "plan", "summary",
        "execution_log", "output_folder", "claimed_at",
    }
    fields, params = [], []
    for key, val in data.items():
        if key in allowed and val is not None:
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
    return await get_task(task_id)


async def cancel_task(task_id: int) -> dict | None:
    return await update_task(task_id, {"status": "cancelled"})


async def claim_next_task() -> dict | None:
    db = await get_db()
    priority_order = "CASE t.priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 END"
    row = await db.execute(
        _TASK_SELECT + f" WHERE t.status = 'pending' ORDER BY {priority_order}, t.created_at ASC LIMIT 1"
    )
    task = await row.fetchone()
    if not task:
        return None
    task = _task_row(task)
    now = _now()
    output_folder = ensure_output_folder(task["id"], task["client_name"], task["project_name"], task["title"])
    await db.execute(
        "UPDATE tasks SET status = 'in_progress', claimed_at = ?, output_folder = ?, updated_at = ? WHERE id = ?",
        (now, output_folder, now, task["id"]),
    )
    await db.commit()
    return await get_task(task["id"])


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
    return await update_task(task_id, {"status": "completed", "summary": summary, "execution_log": execution_log})


async def fail_task(task_id: int, error: str, execution_log: str) -> dict | None:
    task = await get_task(task_id)
    if not task or task["status"] not in ("in_progress", "approved"):
        return None
    return await update_task(task_id, {"status": "failed", "summary": error, "execution_log": execution_log})


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
