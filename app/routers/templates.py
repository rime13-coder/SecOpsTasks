from fastapi import APIRouter, HTTPException
from app.models import TemplateCreate, TemplateUpdate, TemplateOut, TaskOut
from app.services import template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
async def list_templates():
    return await template_service.list_templates()


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(template_id: int):
    tmpl = await template_service.get_template(template_id)
    if not tmpl:
        raise HTTPException(404, "Template not found")
    return tmpl


@router.post("", response_model=TemplateOut, status_code=201)
async def create_template(data: TemplateCreate):
    return await template_service.create_template(data.model_dump())


@router.put("/{template_id}", response_model=TemplateOut)
async def update_template(template_id: int, data: TemplateUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    tmpl = await template_service.update_template(template_id, updates)
    if not tmpl:
        raise HTTPException(404, "Template not found")
    return tmpl


@router.delete("/{template_id}")
async def delete_template(template_id: int):
    ok = await template_service.delete_template(template_id)
    if not ok:
        raise HTTPException(404, "Template not found")
    return {"ok": True}


@router.post("/{template_id}/create-task", response_model=TaskOut, status_code=201)
async def create_task_from_template(template_id: int):
    task = await template_service.create_task_from_template(template_id)
    if not task:
        raise HTTPException(400, "Template not found or missing client/project")
    return task
