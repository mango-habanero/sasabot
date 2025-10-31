from fastapi import APIRouter

from .callback import router as daraja_callback_router

daraja_router = APIRouter()

daraja_router.include_router(
    daraja_callback_router,
    tags=["daraja"],
)
