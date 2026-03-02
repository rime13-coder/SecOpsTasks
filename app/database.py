import aiosqlite
from app.config import DB_PATH, DATA_DIR, SCHEMA_PATH

_db: aiosqlite.Connection | None = None


async def _migrate_clients_projects(db: aiosqlite.Connection):
    """Migrate free-text client/project fields to normalized tables."""
    # Check if migration already done
    cur = await db.execute("PRAGMA table_info(tasks)")
    cols = {r[1] for r in await cur.fetchall()}
    if "client_id" in cols:
        return  # already migrated

    # 1. Populate clients from existing task data
    await db.execute(
        """INSERT OR IGNORE INTO clients (name, description)
           SELECT client_name, COALESCE(MAX(client_description), '')
           FROM tasks
           GROUP BY client_name"""
    )

    # 2. Populate projects from existing task data
    await db.execute(
        """INSERT OR IGNORE INTO projects (client_id, name, description)
           SELECT c.id, t.project_name, COALESCE(MAX(t.project_description), '')
           FROM tasks t
           JOIN clients c ON c.name = t.client_name
           GROUP BY c.id, t.project_name"""
    )

    # 3. Add FK columns to tasks
    await db.execute("ALTER TABLE tasks ADD COLUMN client_id INTEGER REFERENCES clients(id)")
    await db.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER REFERENCES projects(id)")

    # 4. Backfill IDs from name matches
    await db.execute(
        """UPDATE tasks SET client_id = (
               SELECT c.id FROM clients c WHERE c.name = tasks.client_name
           )"""
    )
    await db.execute(
        """UPDATE tasks SET project_id = (
               SELECT p.id FROM projects p
               JOIN clients c ON c.id = p.client_id
               WHERE p.name = tasks.project_name AND c.name = tasks.client_name
           )"""
    )

    await db.commit()


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _db = await aiosqlite.connect(str(DB_PATH))
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        await _db.executescript(schema)
        await _db.commit()
        # Migrations for existing databases
        for col, default in [
            ("client_description", "''"),
            ("project_description", "''"),
        ]:
            try:
                await _db.execute(f"ALTER TABLE tasks ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
                await _db.commit()
            except Exception:
                pass  # column already exists

        # Add new task columns if missing (idempotent)
        for col_sql in [
            "ALTER TABLE tasks ADD COLUMN due_date TEXT",
            "ALTER TABLE tasks ADD COLUMN depends_on TEXT NOT NULL DEFAULT '[]'",
            "ALTER TABLE tasks ADD COLUMN max_retries INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE tasks ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE tasks ADD COLUMN context TEXT NOT NULL DEFAULT '{}'",
            "ALTER TABLE tasks ADD COLUMN recurrence TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE tasks ADD COLUMN source_template_id INTEGER",
            "ALTER TABLE tasks ADD COLUMN progress INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE tasks ADD COLUMN progress_total INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE tasks ADD COLUMN progress_label TEXT NOT NULL DEFAULT ''",
        ]:
            try:
                await _db.execute(col_sql)
                await _db.commit()
            except Exception:
                pass  # column already exists

        # Migrate client/project data to normalized tables
        await _migrate_clients_projects(_db)
    return _db


async def close_db():
    global _db
    if _db is not None:
        await _db.close()
        _db = None
