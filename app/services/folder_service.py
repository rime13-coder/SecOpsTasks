import re
from pathlib import Path
from app.config import CLIENTS_ROOT


def sanitize_name(name: str) -> str:
    """Replace non-alphanumeric chars (except dash/underscore) with underscores."""
    return re.sub(r'[^\w\-]', '_', name).strip('_')


def build_output_folder(task_id: int, client_name: str, project_name: str, title: str) -> Path:
    client_dir = sanitize_name(client_name)
    project_dir = sanitize_name(project_name)
    task_dir = f"Task{task_id:03d}_{sanitize_name(title)}"
    return CLIENTS_ROOT / client_dir / project_dir / task_dir


def ensure_output_folder(task_id: int, client_name: str, project_name: str, title: str) -> str:
    folder = build_output_folder(task_id, client_name, project_name, title)
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder)
