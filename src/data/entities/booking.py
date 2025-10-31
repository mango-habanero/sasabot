"""Booking entity for appointment management."""

from datetime import date, datetime, time

from sqlalchemy import Column, Date, Enum, Time
from sqlmodel import Field

from src.data.entities import Base, IDMixin, TimestampMixin
from src.data.enums import BookingStatus, PaymentStatus


class Booking(Base, IDMixin, TimestampMixin, table=True):
    __tablename__ = "bookings"

    # Booking Reference
    booking_reference: str = Field(unique=True, index=True, max_length=20)

    # Customer Information
    customer_phone: str = Field(index=True, max_length=20)
    customer_name: str | None = Field(default=None, max_length=255)

    # Service Details
    service_category: str = Field(max_length=100)
    service_name: str = Field(max_length=255)
    service_duration: str = Field(max_length=50)

    # Appointment Schedule
    appointment_date: date = Field(sa_column=Column(Date, index=True))
    appointment_time: time = Field(sa_column=Column(Time))
    appointment_datetime_display: str = Field(max_length=255)

    # Financial Details
    service_price: int
    deposit_amount: int
    balance_amount: int
    total_amount: int

    # Status Tracking
    payment_status: PaymentStatus = Field(
        sa_column=Column(Enum(PaymentStatus)), default=PaymentStatus.PENDING
    )
    booking_status: BookingStatus = Field(
        sa_column=Column(Enum(BookingStatus)), default=BookingStatus.PENDING
    )

    # Relationships
    conversation_session_id: int | None = Field(
        default=None, foreign_key="conversation_sessions.id"
    )

    # Payment Tracking
    mpesa_checkout_request_id: str | None = Field(default=None, max_length=255)
    mpesa_receipt_number: str | None = Field(default=None, max_length=50)
    payment_completed_at: datetime | None = Field(default=None)
