"""WhatsApp webhook request DTOs (data coming FROM WhatsApp TO the API)."""

from pydantic import BaseModel, Field

from src.data.enums import MessageType


class WebhookVerificationRequest(BaseModel):
    """Query parameters for webhook verification (GET request from Meta)."""

    hub_mode: str = Field(alias="hub.mode")
    hub_verify_token: str = Field(alias="hub.verify_token")
    hub_challenge: str = Field(alias="hub.challenge")

    class Config:
        populate_by_name = True


class WebhookContact(BaseModel):
    """Contact information from webhook."""

    profile: dict[str, str]  # {"name": "User Name"}
    wa_id: str  # WhatsApp ID (phone number)


class WebhookMessageText(BaseModel):
    """Text content of a message."""

    body: str


class WebhookInteractiveReply(BaseModel):
    """Interactive message reply (button or list selection)."""

    id: str  # The ID of the button/list item selected
    title: str


class WebhookInteractive(BaseModel):
    """Interactive message response."""

    type: str  # "button_reply" or "list_reply"
    button_reply: WebhookInteractiveReply | None = None
    list_reply: WebhookInteractiveReply | None = None


class WebhookMessage(BaseModel):
    """Individual message from webhook."""

    from_: str = Field(alias="from")
    id: str
    timestamp: str
    type: MessageType
    text: WebhookMessageText | None = None
    interactive: WebhookInteractive | None = None

    class Config:
        populate_by_name = True

    @property
    def sender_phone(self) -> str:
        """Get sender phone number."""
        return self.from_

    @property
    def content(self) -> str:
        """Extract message content based on type."""
        if self.text:
            return self.text.body
        elif self.interactive:
            if self.interactive.button_reply:
                return self.interactive.button_reply.id
            elif self.interactive.list_reply:
                return self.interactive.list_reply.id
        return ""


class WebhookStatus(BaseModel):
    """Message status update from webhook."""

    id: str  # Message ID
    status: str  # "sent", "delivered", "read", "failed"
    timestamp: str
    recipient_id: str


class WebhookMetadata(BaseModel):
    """Metadata about the business phone number."""

    display_phone_number: str
    phone_number_id: str


class WebhookValue(BaseModel):
    """Value object containing messages or statuses."""

    messaging_product: str
    metadata: WebhookMetadata
    contacts: list[WebhookContact] | None = None
    messages: list[WebhookMessage] | None = None
    statuses: list[WebhookStatus] | None = None


class WebhookChange(BaseModel):
    """Change object in webhook entry."""

    field: str  # Should be "messages"
    value: WebhookValue


class WebhookEntry(BaseModel):
    """Entry in webhook payload."""

    id: str
    changes: list[WebhookChange]


class WebhookPayload(BaseModel):
    """Root webhook payload from WhatsApp."""

    object: str  # Should be "whatsapp_business_account"
    entry: list[WebhookEntry]

    def extract_messages(self) -> list[WebhookMessage]:
        """Extract all messages from the webhook payload."""
        messages: list[WebhookMessage] = []
        for entry in self.entry:
            for change in entry.changes:
                if change.field == "messages" and change.value.messages:
                    messages.extend(change.value.messages)
        return messages

    def extract_statuses(self) -> list[WebhookStatus]:
        """Extract all status updates from the webhook payload."""
        statuses: list[WebhookStatus] = []
        for entry in self.entry:
            for change in entry.changes:
                if change.field == "messages" and change.value.statuses:
                    statuses.extend(change.value.statuses)
        return statuses

    def extract_contacts(self) -> list[WebhookContact]:
        """Extract all contacts from the webhook payload."""
        contacts: list[WebhookContact] = []
        for entry in self.entry:
            for change in entry.changes:
                if change.field == "messages" and change.value.contacts:
                    contacts.extend(change.value.contacts)
        return contacts
