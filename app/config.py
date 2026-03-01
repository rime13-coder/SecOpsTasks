from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "taskmanager.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
STATIC_DIR = BASE_DIR / "static"
CLIENTS_ROOT = Path(r"C:\ClaudeCollab\Clients")

HOST = "127.0.0.1"
PORT = 8099

STATUSES = ("pending", "in_progress", "approved", "completed", "failed", "cancelled")
PRIORITIES = ("low", "medium", "high", "urgent")
APPROVAL_MODES = ("auto", "ask")
