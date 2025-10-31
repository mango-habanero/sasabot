from fastapi import APIRouter

from .receipts import router as receipts_router

reports_router = APIRouter()

reports_router.include_router(
    receipts_router,
    tags=["receipts"],
)
