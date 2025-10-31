"""Internal DTOs for constructing WhatsApp outbound messages."""

from pydantic import BaseModel, Field


class TextMessage(BaseModel):
    """Text message payload."""

    preview_url: bool = False
    body: str = Field(max_length=4096)


class ButtonReply(BaseModel):
    """Single button definition."""

    type: str = "reply"
    reply: dict[str, str]  # {"id": "button_id", "title": "Button Text"}


class InteractiveAction(BaseModel):
    """Action component for interactive messages."""

    buttons: list[ButtonReply] | None = None
    button: str | None = None  # For list messages - the button text
    sections: list[dict] | None = None  # For list messages


class InteractiveBody(BaseModel):
    """Body text for interactive messages."""

    text: str = Field(max_length=1024)


class InteractiveHeader(BaseModel):
    """Optional header for interactive messages."""

    type: str = "text"
    text: str = Field(max_length=60)


class InteractiveFooter(BaseModel):
    """Optional footer for interactive messages."""

    text: str = Field(max_length=60)


class Interactive(BaseModel):
    """Interactive message with buttons or lists."""

    type: str  # "button" or "list"
    header: InteractiveHeader | None = None
    body: InteractiveBody
    footer: InteractiveFooter | None = None
    action: InteractiveAction


class DocumentMedia(BaseModel):
    """Document media payload."""

    link: str  # Public URL to document
    filename: str
    caption: str | None = Field(default=None, max_length=4096)


class OutboundMessageRequest(BaseModel):
    """Base outbound message request to WhatsApp Cloud API."""

    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str  # Phone number with country code (e.g., "254712345678")
    type: str  # "text", "interactive", "document"
    text: TextMessage | None = None
    interactive: Interactive | None = None
    document: DocumentMedia | None = None
