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

-- Migrations: add columns if they don't exist (ALTER TABLE is idempotent via INSERT OR IGNORE pattern)
-- SQLite doesn't support IF NOT EXISTS on ALTER TABLE, so we catch errors in code.

