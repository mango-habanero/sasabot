"""WhatsApp response DTOs."""

from pydantic import BaseModel


class WhatsAppContact(BaseModel):
    """Contact information in API response."""

    input: str  # Phone number as sent
    wa_id: str  # WhatsApp ID


class WhatsAppMessageResponse(BaseModel):
    """Individual message response."""

    id: str  # WhatsApp-assigned message ID


class WhatsAppAPIResponse(BaseModel):
    """Response from WhatsApp Cloud API after sending a message."""

    messaging_product: str
    contacts: list[WhatsAppContact]
    messages: list[WhatsAppMessageResponse]

    @property
    def message_id(self) -> str:
        """Extract the message ID from response."""
        return self.messages[0].id if self.messages else ""
