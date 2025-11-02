"""Business entity for multi-tenant salon management."""

from sqlalchemy import Column, Enum, Text
from sqlmodel import Field

from src.data.entities import Base, IDMixin, TimestampMixin
from src.data.enums import BusinessStatus


class Business(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "businesses"

    name: str = Field(max_length=255, nullable=False)
    slug: str = Field(max_length=100, nullable=False, unique=True, index=True)
    status: BusinessStatus = Field(
        sa_column=Column(Enum(BusinessStatus)), default=BusinessStatus.ACTIVE
    )
    email: str | None = Field(default=None, max_length=255)
    phone: str = Field(max_length=20, nullable=False)
    instagram_handle: str | None = Field(default=None, max_length=100)
    website: str | None = Field(default=None, max_length=255)
    booking_policy_text: str | None = Field(default=None, sa_column=Column(Text))
    whatsapp_phone_number_id: str = Field(
        max_length=50, nullable=False, unique=True, index=True
    )
