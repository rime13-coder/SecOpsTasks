from fastapi import APIRouter, HTTPException
from app.models import PlanSubmit, CompleteSubmit, FailSubmit, TaskOut
from app.services import task_service

router = APIRouter(prefix="/api/execution", tags=["execution"])


@router.post("/poll")
async def poll_next():
    task = await task_service.claim_next_task()
    if not task:
        return {"task": None}
    return {"task": task}


@router.post("/{task_id}/plan", response_model=TaskOut)
async def submit_plan(task_id: int, data: PlanSubmit):
    task = await task_service.submit_plan(task_id, data.plan)
    if not task:
        raise HTTPException(404, "Task not found or not in_progress")
    return task


@router.post("/{task_id}/approve", response_model=TaskOut)
async def approve_task(task_id: int):
    task = await task_service.approve_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found or not in_progress")
    return task


@router.post("/{task_id}/reject", response_model=TaskOut)
async def reject_task(task_id: int):
    task = await task_service.reject_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found or not in_progress")
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(task_id: int, data: CompleteSubmit):
    task = await task_service.complete_task(task_id, data.summary, data.execution_log)
    if not task:
        raise HTTPException(404, "Task not found or not actionable")
    return task


@router.post("/{task_id}/fail", response_model=TaskOut)
async def fail_task(task_id: int, data: FailSubmit):
    task = await task_service.fail_task(task_id, data.error, data.execution_log)
    if not task:
        raise HTTPException(404, "Task not found or not actionable")
    return task
