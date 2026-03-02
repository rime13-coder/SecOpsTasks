import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import STATIC_DIR
from app.database import get_db, close_db
from app.routers import tasks, clients, execution, manage, templates, webhooks


async def _scheduler_loop():
    """Background loop that creates tasks from recurring templates."""
    from app.services import template_service
    while True:
        try:
            await template_service.run_scheduled_templates()
        except Exception:
            pass
        await asyncio.sleep(60)  # Check every 60 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_db()
    scheduler = asyncio.create_task(_scheduler_loop())
    yield
    scheduler.cancel()
    await close_db()


app = FastAPI(title="SecOps Task Manager", version="1.0.0", lifespan=lifespan)

app.include_router(tasks.router)
app.include_router(clients.router)
app.include_router(execution.router)
app.include_router(manage.router)
app.include_router(templates.router)
app.include_router(webhooks.router)

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
