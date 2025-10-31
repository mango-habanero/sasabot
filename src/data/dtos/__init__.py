"""Data Transfer Objects for API requests and responses."""

from src.data.dtos.requests import (
    ButtonReply,
    DocumentMedia,
    Interactive,
    InteractiveAction,
    InteractiveBody,
    InteractiveFooter,
    InteractiveHeader,
    OutboundMessageRequest,
    TextMessage,
    WebhookMessage,
    WebhookPayload,
    WebhookVerificationRequest,
)
from src.data.dtos.responses import WebhookResponse, WhatsAppAPIResponse

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
    "WhatsAppAPIResponse",
    "WebhookMessage",
    "WebhookPayload",
    "WebhookVerificationRequest",
    "WebhookResponse",
]
