from __future__ import annotations
import json
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.services import task_service


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


_TEMPLATE_SELECT = """
    SELECT t.*, COALESCE(c.name, '') AS client_name, COALESCE(p.name, '') AS project_name
    FROM task_templates t
    LEFT JOIN clients c ON c.id = t.client_id
    LEFT JOIN projects p ON p.id = t.project_id
"""


def _template_row(r) -> dict:
    d = dict(r)
    if isinstance(d.get("context"), str):
        try:
            d["context"] = json.loads(d["context"])
        except (json.JSONDecodeError, TypeError):
            d["context"] = {}
    d["active"] = bool(d.get("active", 1))
    return d


async def list_templates() -> list[dict]:
    db = await get_db()
    rows = await db.execute(_TEMPLATE_SELECT + " ORDER BY t.name")
    return [_template_row(r) for r in await rows.fetchall()]


async def get_template(template_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute(_TEMPLATE_SELECT + " WHERE t.id = ?", (template_id,))
    r = await row.fetchone()
    return _template_row(r) if r else None


async def create_template(data: dict) -> dict:
    db = await get_db()
    now = _now()
    context = json.dumps(data.get("context", {}))
    cur = await db.execute(
        """INSERT INTO task_templates
           (name, client_id, project_id, title, description, required_actions,
            approval_mode, priority, category, due_date_offset,
            max_retries, context, recurrence, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["name"], data.get("client_id"), data.get("project_id"),
            data.get("title", ""), data.get("description", ""),
            data.get("required_actions", ""),
            data.get("approval_mode", "ask"), data.get("priority", "medium"),
            data.get("category", "general"), data.get("due_date_offset"),
            data.get("max_retries", 0), context,
            data.get("recurrence", ""), now, now,
        ),
    )
    await db.commit()
    return await get_template(cur.lastrowid)


async def update_template(template_id: int, data: dict) -> dict | None:
    tmpl = await get_template(template_id)
    if not tmpl:
        return None
    allowed = {
        "name", "client_id", "project_id", "title", "description",
        "required_actions", "approval_mode", "priority", "category",
        "due_date_offset", "max_retries", "context", "recurrence", "active",
    }
    fields, params = [], []
    for key, val in data.items():
        if key not in allowed:
            continue
        if val is None:
            continue
        if key == "context" and isinstance(val, dict):
            val = json.dumps(val)
        if key == "active":
            val = 1 if val else 0
        fields.append(f"{key} = ?")
        params.append(val)
    if not fields:
        return tmpl
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(template_id)
    db = await get_db()
    await db.execute(f"UPDATE task_templates SET {', '.join(fields)} WHERE id = ?", params)
    await db.commit()
    return await get_template(template_id)


async def delete_template(template_id: int) -> bool:
    db = await get_db()
    tmpl = await get_template(template_id)
    if not tmpl:
        return False
    await db.execute("DELETE FROM task_templates WHERE id = ?", (template_id,))
    await db.commit()
    return True


async def create_task_from_template(template_id: int) -> dict | None:
    """Create a new task from a template."""
    tmpl = await get_template(template_id)
    if not tmpl or not tmpl.get("client_id") or not tmpl.get("project_id"):
        return None
    due_date = None
    if tmpl.get("due_date_offset") is not None:
        due_date = (datetime.now(timezone.utc).date() + timedelta(days=tmpl["due_date_offset"])).isoformat()
    data = {
        "client_id": tmpl["client_id"],
        "project_id": tmpl["project_id"],
        "title": tmpl["title"],
        "description": tmpl["description"],
        "required_actions": tmpl["required_actions"],
        "approval_mode": tmpl["approval_mode"],
        "priority": tmpl["priority"],
        "category": tmpl["category"],
        "due_date": due_date,
        "max_retries": tmpl["max_retries"],
        "context": tmpl.get("context", {}),
        "recurrence": tmpl.get("recurrence", ""),
        "source_template_id": tmpl["id"],
    }
    return await task_service.create_task(data)


async def run_scheduled_templates():
    """Check for recurring templates that need new tasks created."""
    db = await get_db()
    rows = await db.execute(
        _TEMPLATE_SELECT + " WHERE t.active = 1 AND t.recurrence != ''"
    )
    templates = [_template_row(r) for r in await rows.fetchall()]
    now = datetime.now(timezone.utc)
    for tmpl in templates:
        if not tmpl.get("client_id") or not tmpl.get("project_id"):
            continue
        recurrence = tmpl["recurrence"]
        last = tmpl.get("last_scheduled_at")
        if last:
            last_dt = datetime.fromisoformat(last).replace(tzinfo=timezone.utc)
        else:
            last_dt = None
        should_create = False
        if last_dt is None:
            should_create = True
        elif recurrence == "daily" and (now - last_dt).days >= 1:
            should_create = True
        elif recurrence == "weekly" and (now - last_dt).days >= 7:
            should_create = True
        elif recurrence == "biweekly" and (now - last_dt).days >= 14:
            should_create = True
        elif recurrence == "monthly" and (now - last_dt).days >= 30:
            should_create = True
        if should_create:
            await create_task_from_template(tmpl["id"])
            await db.execute(
                "UPDATE task_templates SET last_scheduled_at = ? WHERE id = ?",
                (_now(), tmpl["id"]),
            )
            await db.commit()
