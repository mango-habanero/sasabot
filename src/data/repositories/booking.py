"""Repository for Booking entity operations."""

from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.booking import Booking
from src.data.enums import BookingStatus, PaymentStatus


class BookingRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        business_id: int,
        service_id: int,
        booking_reference: str,
        customer_phone: str,
        customer_name: str | None,
        service_category: str,
        service_name: str,
        service_duration: str,
        appointment_date: date,
        appointment_time,
        appointment_datetime_display: str,
        service_price: Decimal,
        deposit_amount: Decimal,
        balance_amount: Decimal,
        total_amount: Decimal,
        conversation_session_id: int | None = None,
    ) -> Booking | None:
        try:
            booking = Booking(
                business_id=business_id,
                service_id=service_id,
                booking_reference=booking_reference,
                customer_phone=customer_phone,
                customer_name=customer_name,
                service_category=service_category,
                service_name=service_name,
                service_duration=service_duration,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_datetime_display=appointment_datetime_display,
                service_price=service_price,
                deposit_amount=deposit_amount,
                balance_amount=balance_amount,
                total_amount=total_amount,
                conversation_session_id=conversation_session_id,
            )

            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)

            app_logger.info(
                "Booking created",
                booking_id=booking.id,
                business_id=business_id,
                service_id=service_id,
                booking_reference=booking_reference,
                customer_phone=customer_phone,
                service_name=service_name,
                appointment_date=str(appointment_date),
            )
            return booking

        except Exception as e:
            self.session.rollback()
            app_logger.error(
                "Failed to create booking",
                error=str(e),
                business_id=business_id,
                booking_reference=booking_reference,
            )
            return None

    def get_by_id(self, booking_id: int) -> Booking | None:
        return self.session.get(Booking, booking_id)

    def get_by_reference(self, reference: str) -> Booking | None:
        statement = select(Booking).where(Booking.booking_reference == reference)
        return self.session.exec(statement).first()

    def get_by_checkout_request_id(self, checkout_request_id: str) -> Booking | None:
        statement = select(Booking).where(
            Booking.mpesa_checkout_request_id == checkout_request_id
        )
        return self.session.exec(statement).first()

    def get_by_phone(self, phone_number: str, limit: int = 10) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.customer_phone == phone_number)
            .order_by(col(Booking.created_at).desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_by_date(self, target_date: date) -> list[Booking]:
        statement = (
            select(Booking)
            .where(Booking.appointment_date == target_date)
            .order_by(Booking.appointment_time)
        )
        return list(self.session.exec(statement).all())

    def update_payment_status(
        self,
        booking_id: int,
        status: PaymentStatus,
        checkout_request_id: str | None = None,
        receipt_number: str | None = None,
    ) -> bool:
        booking = self.session.get(Booking, booking_id)
        if not booking:
            app_logger.warning(
                "Booking not found for payment status update",
                booking_id=booking_id,
            )
            return False

        booking.payment_status = status

        if checkout_request_id:
            booking.mpesa_checkout_request_id = checkout_request_id

        if receipt_number:
            booking.mpesa_receipt_number = receipt_number

        if status == PaymentStatus.PAID:
            booking.booking_status = BookingStatus.CONFIRMED
            from datetime import datetime, timezone

            booking.payment_completed_at = datetime.now(timezone.utc)

        self.session.commit()

        app_logger.info(
            "Payment status updated",
            booking_id=booking_id,
            booking_reference=booking.booking_reference,
            payment_status=status.value,
            booking_status=booking.booking_status.value,
        )
        return True

    def update_booking_status(
        self,
        booking_id: int,
        status: BookingStatus,
    ) -> bool:
        booking = self.session.get(Booking, booking_id)
        if not booking:
            app_logger.warning(
                "Booking not found for status update",
                booking_id=booking_id,
            )
            return False

        booking.booking_status = status
        self.session.commit()

        app_logger.info(
            "Booking status updated",
            booking_id=booking_id,
            booking_reference=booking.booking_reference,
            booking_status=status.value,
        )
        return True

    def cancel_booking(self, booking_id: int) -> bool:
        return self.update_booking_status(booking_id, BookingStatus.CANCELLED)
