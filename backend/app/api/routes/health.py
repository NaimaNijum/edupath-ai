from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import AsyncSessionLocal

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    database = "unhealthy"

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            database = "healthy"
    except Exception:
        pass

    return {
        "status": "healthy",
        "service": "edupath-api",
        "database": database,
    }