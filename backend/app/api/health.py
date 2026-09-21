from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine

router = APIRouter()


@router.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@router.get("/db-health")
def db_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "connected"
        }

    except Exception as e:
        return {
            "database": "failed",
            "error": str(e)
        }