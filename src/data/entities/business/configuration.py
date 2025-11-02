"""Business configuration entity for operational settings."""

from sqlalchemy import JSON, Column
from sqlmodel import Field

from src.data.entities.base import Base, IDMixin, TimestampMixin


class Configuration(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "configurations"

    business_id: int = Field(
        foreign_key="businesses.id",
        nullable=False,
        unique=True,
        index=True,
        ondelete="CASCADE",
    )
    deposit_percentage: float = Field(default=30.0, nullable=False, ge=0, le=100)
    cancellation_window_hours: int = Field(default=6, nullable=False, ge=0)
    accepted_payment_methods: list = Field(
        default_factory=lambda: ["mpesa"], sa_column=Column(JSON)
    )
    booking_advance_days: int = Field(default=30, nullable=False, gt=0)
    slot_duration_minutes: int = Field(default=15, nullable=False, gt=0)
    buffer_time_minutes: int = Field(default=0, nullable=False, ge=0)
    auto_confirm_bookings: bool = Field(default=False, nullable=False)
    custom_settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
