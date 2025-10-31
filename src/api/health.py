from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from src.common.dependencies import get_session
from src.configuration import app_logger

health_check_router = APIRouter(tags=["system"])


@health_check_router.get("/health")
async def health_check(session: Session = Depends(get_session)) -> dict:
    try:
        session.exec(select(1)).first()
        database_status = "healthy"
    except Exception as e:
        app_logger.error("Database health check failed", error=str(e))
        database_status = "unhealthy"

    return {
        "status": "healthy" if database_status == "healthy" else "degraded",
        "database": database_status,
    }
