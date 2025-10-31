"""SasaBot APIs,"""

from fastapi import APIRouter

from src.configuration import settings

from .health import health_check_router
from .payment import payment_router
from .reports import reports_router
from .whatsapp import whatsapp_router

api_router = APIRouter()

api_router.include_router(health_check_router, prefix=settings.API_PREFIX)
api_router.include_router(payment_router, prefix=settings.API_PREFIX)
api_router.include_router(reports_router, prefix=settings.API_PREFIX)
api_router.include_router(whatsapp_router, prefix=settings.API_PREFIX)
