from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import (
    ClientCreate, ClientUpdate, ClientOut,
    ProjectCreate, ProjectUpdate, ProjectOut,
)
from app.services import client_service

router = APIRouter(prefix="/api/manage", tags=["manage"])


# ── Clients ──────────────────────────────────────────────

@router.get("/clients", response_model=list[ClientOut])
async def list_clients():
    return await client_service.list_clients()


@router.post("/clients", response_model=ClientOut, status_code=201)
async def create_client(data: ClientCreate):
    return await client_service.create_client(data.model_dump())


@router.get("/clients/{client_id}", response_model=ClientOut)
async def get_client(client_id: int):
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@router.put("/clients/{client_id}", response_model=ClientOut)
async def update_client(client_id: int, data: ClientUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    client = await client_service.update_client(client_id, updates)
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@router.delete("/clients/{client_id}")
async def delete_client(client_id: int):
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    ok = await client_service.delete_client(client_id)
    if not ok:
        raise HTTPException(409, "Cannot delete client with existing projects")
    return {"ok": True}


@router.get("/clients/{client_id}/projects", response_model=list[ProjectOut])
async def list_client_projects(client_id: int):
    return await client_service.list_projects(client_id=client_id)


# ── Projects ─────────────────────────────────────────────

@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(client_id: Optional[int] = Query(None)):
    return await client_service.list_projects(client_id=client_id)


@router.post("/projects", response_model=ProjectOut, status_code=201)
async def create_project(data: ProjectCreate):
    return await client_service.create_project(data.model_dump())


@router.get("/projects/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int):
    project = await client_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.put("/projects/{project_id}", response_model=ProjectOut)
async def update_project(project_id: int, data: ProjectUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    project = await client_service.update_project(project_id, updates)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    project = await client_service.get_project(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    ok = await client_service.delete_project(project_id)
    if not ok:
        raise HTTPException(409, "Cannot delete project with existing tasks")
    return {"ok": True}
