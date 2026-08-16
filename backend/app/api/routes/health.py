from fastapi import APIRouter
from sqlalchemy import text

from app.database.session import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "service": "edupath-api",
            "database": "healthy",
        }

    except Exception as exc:
        return {
            "status": "healthy",
            "service": "edupath-api",
            "database": "unhealthy",
            "database_error": str(exc),
        }