"""WhatsApp APIs"""

from fastapi import APIRouter

from .webhooks import router as webhooks_router

whatsapp_router = APIRouter()

whatsapp_router.include_router(
    webhooks_router,
    tags=["webhooks"],
)
