from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import STATIC_DIR
from app.database import get_db, close_db
from app.routers import tasks, clients, execution, manage


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_db()
    yield
    await close_db()


app = FastAPI(title="SecOps Task Manager", version="1.0.0", lifespan=lifespan)

app.include_router(tasks.router)
app.include_router(clients.router)
app.include_router(execution.router)
app.include_router(manage.router)

app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
