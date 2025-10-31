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
    "TextMessage",
    "WebhookMessage",
    "WebhookPayload",
    "WebhookVerificationRequest",
]
