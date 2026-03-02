from __future__ import annotations
import json
from datetime import datetime, timezone
from app.database import get_db


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _webhook_row(r) -> dict:
    d = dict(r)
    if isinstance(d.get("events"), str):
        try:
            d["events"] = json.loads(d["events"])
        except (json.JSONDecodeError, TypeError):
            d["events"] = []
    d["active"] = bool(d.get("active", 1))
    return d


async def list_webhooks() -> list[dict]:
    db = await get_db()
    rows = await db.execute("SELECT * FROM webhooks ORDER BY id")
    return [_webhook_row(r) for r in await rows.fetchall()]


async def get_webhook(webhook_id: int) -> dict | None:
    db = await get_db()
    row = await db.execute("SELECT * FROM webhooks WHERE id = ?", (webhook_id,))
    r = await row.fetchone()
    return _webhook_row(r) if r else None


async def create_webhook(data: dict) -> dict:
    db = await get_db()
    now = _now()
    events = json.dumps(data.get("events", []))
    cur = await db.execute(
        """INSERT INTO webhooks (url, events, secret, active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (data["url"], events, data.get("secret", ""),
         1 if data.get("active", True) else 0, now, now),
    )
    await db.commit()
    return await get_webhook(cur.lastrowid)


async def update_webhook(webhook_id: int, data: dict) -> dict | None:
    wh = await get_webhook(webhook_id)
    if not wh:
        return None
    fields, params = [], []
    for key in ("url", "events", "secret", "active"):
        if key not in data or data[key] is None:
            continue
        val = data[key]
        if key == "events" and isinstance(val, list):
            val = json.dumps(val)
        if key == "active":
            val = 1 if val else 0
        fields.append(f"{key} = ?")
        params.append(val)
    if not fields:
        return wh
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(webhook_id)
    db = await get_db()
    await db.execute(f"UPDATE webhooks SET {', '.join(fields)} WHERE id = ?", params)
    await db.commit()
    return await get_webhook(webhook_id)


async def delete_webhook(webhook_id: int) -> bool:
    db = await get_db()
    wh = await get_webhook(webhook_id)
    if not wh:
        return False
    await db.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
    await db.commit()
    return True
