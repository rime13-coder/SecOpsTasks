from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import TaskCreate, TaskUpdate, TaskOut, StatsOut
from app.services import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    status: Optional[str] = Query(None),
    client: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    return await task_service.list_tasks(status=status, client=client, project=project, category=category, search=search)


@router.get("/stats", response_model=StatsOut)
async def get_stats():
    return await task_service.get_stats()


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int):
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post("", response_model=TaskOut, status_code=201)
async def create_task(data: TaskCreate):
    return await task_service.create_task(data.model_dump())


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(task_id: int, data: TaskUpdate):
    nullable_fields = {"claimed_at", "due_date", "depends_on", "context"}
    raw = data.model_dump()
    updates = {k: v for k, v in raw.items() if v is not None or k in nullable_fields}
    # Remove fields that weren't explicitly set (still None and not in the request body)
    sent_fields = data.model_fields_set
    updates = {k: v for k, v in updates.items() if k in sent_fields}
    task = await task_service.update_task(task_id, updates)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.delete("/{task_id}", response_model=TaskOut)
async def delete_task(task_id: int):
    task = await task_service.cancel_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.post("/{task_id}/destroy", status_code=204)
async def destroy_task(task_id: int):
    ok = await task_service.destroy_task(task_id)
    if not ok:
        raise HTTPException(404, "Task not found")
