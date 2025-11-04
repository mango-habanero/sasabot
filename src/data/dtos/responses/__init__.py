"""Response DTOs."""

from .api import ErrorDetail, ErrorResponse
from .daraja import AccessTokenResponse, DarajaCallbackPayload, STKPushResponse
from .webhook import WebhookResponse
from .whatsapp import (
    GranularScope,
    TokenDebugData,
    TokenDebugResponse,
    WhatsAppAPIResponse,
    WhatsAppContact,
    WhatsAppMessageResponse,
)

__all__ = [
    "AccessTokenResponse",
    "DarajaCallbackPayload",
    "ErrorDetail",
    "ErrorResponse",
    "GranularScope",
    "STKPushResponse",
    "TokenDebugData",
    "TokenDebugResponse",
    "WhatsAppAPIResponse",
    "WhatsAppContact",
    "WhatsAppMessageResponse",
    "WebhookResponse",
]
