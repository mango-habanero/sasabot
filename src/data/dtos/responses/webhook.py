"""WhatsApp webhook response DTOs (data going FROM the API TO WhatsApp)."""

from pydantic import BaseModel


class WebhookResponse(BaseModel):
    """Standard webhook acknowledgment response."""

    status: str = "ok"
