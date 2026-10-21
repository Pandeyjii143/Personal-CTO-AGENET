from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.api.health import router as health_router
from app.db.init_db import create_tables
from app.api.projects import router as project_router
from app.api.blueprints import ( router as blueprint_router)
from app.api.milestones import (router as milestone_router)
from app.api.tasks import (
    router as task_router
)
from app.core.config import settings
from app.api.ai_test import ai_test_router
from app.api.repair import repair_router
from app.api.generation import router as generation_router





@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(project_router)
app.include_router(blueprint_router)
app.include_router(milestone_router)
app.include_router(task_router)
app.include_router(ai_test_router)
app.include_router(repair_router)
app.include_router(generation_router)



@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} Backend Running"
    }