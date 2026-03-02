from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# --- Client / Project management models ---

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = ""

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ClientOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: str
    updated_at: str

class ProjectCreate(BaseModel):
    client_id: int
    name: str = Field(..., min_length=1)
    description: str = ""

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectOut(BaseModel):
    id: int
    client_id: int
    client_name: str = ""
    name: str
    description: str
    created_at: str
    updated_at: str


# --- Task models ---

class TaskCreate(BaseModel):
    client_id: int
    project_id: int
    title: str = Field(..., min_length=1)
    description: str = ""
    required_actions: str = ""
    approval_mode: str = "ask"
    priority: str = "medium"
    category: str = "general"
    due_date: Optional[str] = None
    depends_on: list[int] = []
    max_retries: int = 0
    context: dict = {}
    recurrence: str = ""


class TaskUpdate(BaseModel):
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required_actions: Optional[str] = None
    approval_mode: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None
    summary: Optional[str] = None
    execution_log: Optional[str] = None
    due_date: Optional[str] = None
    depends_on: Optional[list[int]] = None
    max_retries: Optional[int] = None
    context: Optional[dict] = None
    recurrence: Optional[str] = None
    progress: Optional[int] = None
    progress_total: Optional[int] = None
    progress_label: Optional[str] = None


class PlanSubmit(BaseModel):
    plan: str = Field(..., min_length=1)


class CompleteSubmit(BaseModel):
    summary: str = ""
    execution_log: str = ""


class FailSubmit(BaseModel):
    error: str = ""
    execution_log: str = ""


class ProgressUpdate(BaseModel):
    progress: int = 0
    progress_total: int = 0
    progress_label: str = ""


class TaskOut(BaseModel):
    id: int
    client_name: str
    client_description: str
    project_name: str
    project_description: str
    title: str
    description: str
    required_actions: str
    approval_mode: str
    status: str
    priority: str
    category: str
    due_date: Optional[str] = None
    depends_on: list[int] = []
    max_retries: int = 0
    retry_count: int = 0
    context: dict = {}
    recurrence: str = ""
    source_template_id: Optional[int] = None
    progress: int = 0
    progress_total: int = 0
    progress_label: str = ""
    plan: str
    summary: str
    execution_log: str
    output_folder: str
    claimed_at: Optional[str]
    created_at: str
    updated_at: str


class CategoryOut(BaseModel):
    category: str
    approval_mode: str
    description: str


class StatsOut(BaseModel):
    pending: int
    in_progress: int
    approved: int
    completed: int
    failed: int
    cancelled: int


# --- Template models ---

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1)
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    title: str = ""
    description: str = ""
    required_actions: str = ""
    approval_mode: str = "ask"
    priority: str = "medium"
    category: str = "general"
    due_date_offset: Optional[int] = None
    max_retries: int = 0
    context: dict = {}
    recurrence: str = ""


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required_actions: Optional[str] = None
    approval_mode: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    due_date_offset: Optional[int] = None
    max_retries: Optional[int] = None
    context: Optional[dict] = None
    recurrence: Optional[str] = None
    active: Optional[bool] = None


class TemplateOut(BaseModel):
    id: int
    name: str
    client_id: Optional[int] = None
    project_id: Optional[int] = None
    client_name: str = ""
    project_name: str = ""
    title: str
    description: str
    required_actions: str
    approval_mode: str
    priority: str
    category: str
    due_date_offset: Optional[int] = None
    max_retries: int
    context: dict = {}
    recurrence: str
    active: bool = True
    last_scheduled_at: Optional[str] = None
    created_at: str
    updated_at: str


# --- Webhook models ---

class WebhookCreate(BaseModel):
    url: str = Field(..., min_length=1)
    events: list[str] = []
    secret: str = ""
    active: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[list[str]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None


class WebhookOut(BaseModel):
    id: int
    url: str
    events: list[str] = []
    secret: str
    active: bool
    created_at: str
    updated_at: str
