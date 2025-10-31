from fastapi import APIRouter

from .daraja import daraja_callback_router

payment_router = APIRouter()

payment_router.include_router(
    daraja_callback_router,
    tags=["payments"],
)
