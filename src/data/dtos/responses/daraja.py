"""Daraja API response DTOs."""

from pydantic import BaseModel, ConfigDict, Field


class AccessTokenResponse(BaseModel):
    """OAuth access token response."""

    access_token: str
    expires_in: str


class STKPushResponse(BaseModel):
    """STK Push initiation response."""

    merchant_request_id: str = Field(alias="MerchantRequestID")
    checkout_request_id: str = Field(alias="CheckoutRequestID")
    response_code: str = Field(alias="ResponseCode")
    response_description: str = Field(alias="ResponseDescription")
    customer_message: str = Field(alias="CustomerMessage")

    model_config = ConfigDict(populate_by_name=True)


class CallbackMetadataItem(BaseModel):
    """Single item in callback metadata."""

    name: str = Field(alias="Name")
    value: int | str | None = Field(default=None, alias="Value")

    model_config = ConfigDict(populate_by_name=True)


class CallbackMetadata(BaseModel):
    """Callback metadata containing transaction details."""

    items: list[CallbackMetadataItem] = Field(alias="Item")

    model_config = ConfigDict(populate_by_name=True)


class STKCallback(BaseModel):
    """STK Push callback data."""

    merchant_request_id: str = Field(alias="MerchantRequestID")
    checkout_request_id: str = Field(alias="CheckoutRequestID")
    result_code: int = Field(alias="ResultCode")
    result_desc: str = Field(alias="ResultDesc")
    callback_metadata: CallbackMetadata | None = Field(
        default=None, alias="CallbackMetadata"
    )

    model_config = ConfigDict(populate_by_name=True)


class CallbackBody(BaseModel):
    """Callback body wrapper."""

    stk_callback: STKCallback = Field(alias="stkCallback")

    model_config = ConfigDict(populate_by_name=True)


class DarajaCallbackPayload(BaseModel):
    """Root callback payload from Daraja."""

    body: CallbackBody = Field(alias="Body")

    model_config = ConfigDict(populate_by_name=True)

    def get_amount(self) -> int | None:
        """Extract amount from callback metadata."""
        if not self.body.stk_callback.callback_metadata:
            return None

        for item in self.body.stk_callback.callback_metadata.items:
            if item.name == "Amount":
                return int(item.value) if item.value else None
        return None

    def get_receipt_number(self) -> str | None:
        """Extract M-Pesa receipt number from callback metadata."""
        if not self.body.stk_callback.callback_metadata:
            return None

        for item in self.body.stk_callback.callback_metadata.items:
            if item.name == "MpesaReceiptNumber":
                return str(item.value) if item.value else None
        return None

    def get_phone_number(self) -> str | None:
        """Extract phone number from callback metadata."""
        if not self.body.stk_callback.callback_metadata:
            return None

        for item in self.body.stk_callback.callback_metadata.items:
            if item.name == "PhoneNumber":
                return str(item.value) if item.value else None
        return None

    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.body.stk_callback.result_code == 0
