"""Repository for Booking entity operations."""

from datetime import date

from sqlmodel import Session, col, select

from src.configuration import app_logger
from src.data.entities.booking import Booking
from src.data.enums import BookingStatus, PaymentStatus


class BookingRepository:
    """Repository for Booking entity operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, booking_data: dict) -> Booking | None:
        try:
            booking = Booking(**booking_data)

            self.session.add(booking)
            self.session.commit()
            self.session.refresh(booking)

            app_logger.info(
                "Booking created",
                booking_id=booking.id,
                booking_reference=booking.booking_reference,
                customer_phone=booking.customer_phone,
                service_name=booking.service_name,
                appointment_date=str(booking.appointment_date),
            )
            return booking

        except Exception as e:
            self.session.rollback()
            app_logger.error(
                "Failed to create booking",
                error=str(e),
                booking_data=booking_data,
            )
            return None

    def get_by_reference(self, reference: str) -> Booking | None:
        statement = select(Booking).where(Booking.booking_reference == reference)
        return self.session.exec(statement).first()

    def get_by_checkout_request_id(self, checkout_request_id: str) -> Booking | None:
        statement = select(Booking).where(
            Booking.mpesa_checkout_request_id == checkout_request_id
        )
        return self.session.exec(statement).first()

    def get_by_id(self, booking_id: int) -> Booking | None:
        return self.session.get(Booking, booking_id)

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

        # If payment successful, update booking status and timestamp
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
