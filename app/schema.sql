CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL REFERENCES clients(id),
    name        TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(client_id, name)
);

CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name     TEXT    NOT NULL,
    client_description TEXT NOT NULL DEFAULT '',
    project_name    TEXT    NOT NULL,
    project_description TEXT NOT NULL DEFAULT '',
    title           TEXT    NOT NULL,
    description     TEXT    NOT NULL DEFAULT '',
    required_actions TEXT   NOT NULL DEFAULT '',
    approval_mode   TEXT    NOT NULL DEFAULT 'ask' CHECK(approval_mode IN ('auto','ask')),
    status          TEXT    NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','in_progress','approved','completed','failed','cancelled')),
    priority        TEXT    NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high','urgent')),
    category        TEXT    NOT NULL DEFAULT 'general',
    due_date        TEXT,
    depends_on      TEXT    NOT NULL DEFAULT '[]',
    max_retries     INTEGER NOT NULL DEFAULT 0,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    context         TEXT    NOT NULL DEFAULT '{}',
    recurrence      TEXT    NOT NULL DEFAULT '',
    source_template_id INTEGER,
    progress        INTEGER NOT NULL DEFAULT 0,
    progress_total  INTEGER NOT NULL DEFAULT 0,
    progress_label  TEXT    NOT NULL DEFAULT '',
    plan            TEXT    NOT NULL DEFAULT '',
    summary         TEXT    NOT NULL DEFAULT '',
    execution_log   TEXT    NOT NULL DEFAULT '',
    output_folder   TEXT    NOT NULL DEFAULT '',
    claimed_at      TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS category_defaults (
    category      TEXT PRIMARY KEY,
    approval_mode TEXT NOT NULL DEFAULT 'ask' CHECK(approval_mode IN ('auto','ask')),
    description   TEXT NOT NULL DEFAULT ''
);

-- Seed SecOps categories
INSERT OR IGNORE INTO category_defaults (category, approval_mode, description) VALUES
    ('documentation', 'auto', 'Documentation and knowledge base updates'),
    ('template',      'auto', 'Template creation and boilerplate generation'),
    ('report',        'ask',  'Client reports and deliverables'),
    ('log_analysis',  'ask',  'Security log analysis and correlation'),
    ('script',        'ask',  'Script development and automation'),
    ('presentation',  'ask',  'Presentations and slide decks'),
    ('remediation',   'ask',  'Remediation plans and implementation'),
    ('compliance',    'ask',  'Compliance checks and audit preparation'),
    ('recon',         'ask',  'Reconnaissance and OSINT gathering'),
    ('general',       'ask',  'General tasks');

CREATE TABLE IF NOT EXISTS task_templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL UNIQUE,
    client_id       INTEGER REFERENCES clients(id),
    project_id      INTEGER REFERENCES projects(id),
    title           TEXT    NOT NULL DEFAULT '',
    description     TEXT    NOT NULL DEFAULT '',
    required_actions TEXT   NOT NULL DEFAULT '',
    approval_mode   TEXT    NOT NULL DEFAULT 'ask' CHECK(approval_mode IN ('auto','ask')),
    priority        TEXT    NOT NULL DEFAULT 'medium' CHECK(priority IN ('low','medium','high','urgent')),
    category        TEXT    NOT NULL DEFAULT 'general',
    due_date_offset INTEGER,
    max_retries     INTEGER NOT NULL DEFAULT 0,
    context         TEXT    NOT NULL DEFAULT '{}',
    recurrence      TEXT    NOT NULL DEFAULT '',
    active          INTEGER NOT NULL DEFAULT 1,
    last_scheduled_at TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS webhooks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    url         TEXT    NOT NULL,
    events      TEXT    NOT NULL DEFAULT '[]',
    secret      TEXT    NOT NULL DEFAULT '',
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Migrations: add columns if they don't exist (ALTER TABLE is idempotent via INSERT OR IGNORE pattern)
-- SQLite doesn't support IF NOT EXISTS on ALTER TABLE, so we catch errors in code.

