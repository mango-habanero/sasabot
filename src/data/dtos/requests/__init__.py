"""Request DTOs."""

from .webhook import (
    WebhookMessage,
    WebhookPayload,
    WebhookVerificationRequest,
)
from .whatsapp import (
    ButtonReply,
    DocumentMedia,
    Interactive,
    InteractiveAction,
    InteractiveBody,
    InteractiveFooter,
    InteractiveHeader,
    OutboundMessageRequest,
    TextMessage,
    TokenDebugRequest,
    TokenExchangeRequest,
)

__all__ = [
    "ButtonReply",
    "DocumentMedia",
    "Interactive",
    "InteractiveAction",
    "InteractiveBody",
    "InteractiveFooter",
    "InteractiveHeader",
    "OutboundMessageRequest",
    "TokenDebugRequest",
    "TokenExchangeRequest",
    "TextMessage",
    "WebhookMessage",
    "WebhookPayload",
    "WebhookVerificationRequest",
]
