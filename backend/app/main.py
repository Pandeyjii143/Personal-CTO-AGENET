from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.api.health import router as health_router
from app.db.init_db import create_tables
from app.api.projects import router as project_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.include_router(health_router)
app.include_router(project_router)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} Backend Running"
    }