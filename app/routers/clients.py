from fastapi import APIRouter
from app.models import CategoryOut
from app.services import client_service, task_service

router = APIRouter(prefix="/api", tags=["lookups"])


@router.get("/clients", response_model=list[str])
async def get_clients():
    return await client_service.get_client_names()


@router.get("/clients/{name}/projects", response_model=list[str])
async def get_projects(name: str):
    return await client_service.get_project_names_for_client(name)


@router.get("/categories", response_model=list[CategoryOut])
async def get_categories():
    return await task_service.get_categories()
