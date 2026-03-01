from __future__ import annotations
from datetime import datetime, timezone
from app.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ── Clients ──────────────────────────────────────────────

async def list_clients() -> list[dict]:
    db = await get_db()
    rows = await db.execute("SELECT * FROM clients ORDER BY name")
    return [dict(r) for r in await rows.fetchall()]


async def get_client(client_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
    r = await row.fetchone()
    return dict(r) if r else None


async def create_client(data: dict) -> dict:
    db = await get_db()
    now = _now()
    cur = await db.execute(
        "INSERT INTO clients (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (data["name"], data.get("description", ""), now, now),
    )
    await db.commit()
    return await get_client(cur.lastrowid)


async def update_client(client_id: int, data: dict) -> dict | None:
    client = await get_client(client_id)
    if not client:
        return None
    fields, params = [], []
    for key in ("name", "description"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return client
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(client_id)
    db = await get_db()
    await db.execute(f"UPDATE clients SET {', '.join(fields)} WHERE id = ?", params)
    await db.commit()
    return await get_client(client_id)


async def delete_client(client_id: int) -> bool:
    """Delete client. Returns False if it has projects."""
    db = await get_db()
    row = await db.execute("SELECT COUNT(*) FROM projects WHERE client_id = ?", (client_id,))
    count = (await row.fetchone())[0]
    if count > 0:
        return False
    await db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    await db.commit()
    return True


# ── Projects ─────────────────────────────────────────────

async def list_projects(client_id: int | None = None) -> list[dict]:
    db = await get_db()
    if client_id is not None:
        rows = await db.execute(
            """SELECT p.*, c.name AS client_name
               FROM projects p JOIN clients c ON c.id = p.client_id
               WHERE p.client_id = ? ORDER BY p.name""",
            (client_id,),
        )
    else:
        rows = await db.execute(
            """SELECT p.*, c.name AS client_name
               FROM projects p JOIN clients c ON c.id = p.client_id
               ORDER BY c.name, p.name"""
        )
    return [dict(r) for r in await rows.fetchall()]


async def get_project(project_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute(
        """SELECT p.*, c.name AS client_name
           FROM projects p JOIN clients c ON c.id = p.client_id
           WHERE p.id = ?""",
        (project_id,),
    )
    r = await row.fetchone()
    return dict(r) if r else None


async def create_project(data: dict) -> dict:
    db = await get_db()
    now = _now()
    cur = await db.execute(
        "INSERT INTO projects (client_id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (data["client_id"], data["name"], data.get("description", ""), now, now),
    )
    await db.commit()
    return await get_project(cur.lastrowid)


async def update_project(project_id: int, data: dict) -> dict | None:
    project = await get_project(project_id)
    if not project:
        return None
    fields, params = [], []
    for key in ("name", "description"):
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            params.append(data[key])
    if not fields:
        return project
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(project_id)
    db = await get_db()
    await db.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", params)
    await db.commit()
    return await get_project(project_id)


async def delete_project(project_id: int) -> bool:
    """Delete project. Returns False if it has tasks."""
    db = await get_db()
    row = await db.execute("SELECT COUNT(*) FROM tasks WHERE project_id = ?", (project_id,))
    count = (await row.fetchone())[0]
    if count > 0:
        return False
    await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    await db.commit()
    return True


# ── Lookup helpers (used by existing /api/clients endpoints) ──

async def get_client_names() -> list[str]:
    db = await get_db()
    rows = await db.execute("SELECT name FROM clients ORDER BY name")
    return [r["name"] for r in await rows.fetchall()]


async def get_project_names_for_client(client_name: str) -> list[str]:
    db = await get_db()
    rows = await db.execute(
        """SELECT p.name FROM projects p
           JOIN clients c ON c.id = p.client_id
           WHERE c.name = ? ORDER BY p.name""",
        (client_name,),
    )
    return [r["name"] for r in await rows.fetchall()]
