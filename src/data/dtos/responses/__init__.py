"""Response DTOs."""

from .api import ErrorDetail, ErrorResponse
from .daraja import AccessTokenResponse, DarajaCallbackPayload, STKPushResponse
from .webhook import WebhookResponse
from .whatsapp import WhatsAppAPIResponse

__all__ = [
    "AccessTokenResponse",
    "DarajaCallbackPayload",
    "ErrorDetail",
    "ErrorResponse",
    "STKPushResponse",
    "WebhookResponse",
    "WhatsAppAPIResponse",
]
