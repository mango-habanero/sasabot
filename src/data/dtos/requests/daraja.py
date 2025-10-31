"""Daraja API request DTOs."""

from pydantic import BaseModel, ConfigDict, Field


class STKPushRequest(BaseModel):
    """STK Push request to initiate M-Pesa payment."""

    business_short_code: str = Field(alias="BusinessShortCode")
    password: str = Field(alias="Password")
    timestamp: str = Field(alias="Timestamp")
    transaction_type: str = Field(
        default="CustomerPayBillOnline", alias="TransactionType"
    )
    amount: str = Field(alias="Amount")
    party_a: str = Field(alias="PartyA")  # Customer phone
    party_b: str = Field(alias="PartyB")  # Business shortcode
    phone_number: str = Field(alias="PhoneNumber")  # Customer phone
    call_back_url: str = Field(alias="CallBackURL")
    account_reference: str = Field(alias="AccountReference")  # Booking reference
    transaction_desc: str = Field(alias="TransactionDesc")

    model_config = ConfigDict(populate_by_name=True)
