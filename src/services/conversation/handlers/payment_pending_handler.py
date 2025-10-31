"""Handler for PAYMENT_PENDING state."""

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums import PaymentStatus
from src.data.enums.conversation import ConversationState
from src.data.repositories.booking import BookingRepository
from src.services.conversation.handlers.base import BaseStateHandler


def _handle_payment_success(
    booking,
    customer_name: str | None = None,
) -> dict:
    app_logger.info(
        "Payment successful, confirming to user",
        booking_id=booking.id,
        booking_reference=booking.booking_reference,
    )

    greeting = f"{customer_name}!" if customer_name else "there!"

    message = (
        f"✅ **Payment Confirmed!**\n\n"
        f"Thank you, {greeting}\n\n"
        f"Your booking is confirmed:\n"
        f"📋 Reference: {booking.booking_reference}\n"
        f"💳 Receipt: {booking.mpesa_receipt_number or 'Processing'}\n"
        f"📅 Appointment: {booking.appointment_datetime_display}\n\n"
        f"We look forward to seeing you! 💅✨\n\n"
        f"Need anything else? Just let me know!"
    )

    return {
        "text": message,
        "update_context": {},
        "transition_to": ConversationState.IDLE,
    }


def _handle_payment_failure(
    booking,
) -> dict:
    app_logger.info(
        "Payment failed, offering retry options",
        booking_id=booking.id,
        booking_reference=booking.booking_reference,
    )

    message = (
        f"❌ **Payment Not Completed**\n\n"
        f"Your payment could not be processed.\n\n"
        f"📋 Booking Reference: {booking.booking_reference}\n\n"
        f"What would you like to do?"
    )

    return {
        "buttons": {
            "body": message,
            "buttons": [
                ("retry_same_number", "🔄 Try Again"),
                ("retry_different_number", "📱 Use Different Number"),
                ("cancel_payment", "❌ Cancel Booking"),
            ],
            "footer": "Choose an option to continue",
        },
    }


def _handle_still_pending(
    booking,
) -> dict:
    app_logger.info(
        "Payment still pending",
        booking_id=booking.id,
        booking_reference=booking.booking_reference,
    )

    message = (
        f"⏳ **Payment Processing...**\n\n"
        f"We're waiting for your M-Pesa payment confirmation.\n\n"
        f"📋 Reference: {booking.booking_reference}\n"
        f"💰 Amount: KES {booking.deposit_amount:,}\n\n"
        f"Please check your phone for the M-Pesa prompt and enter your PIN.\n\n"
        f"⏱️ This may take up to 60 seconds.\n\n"
        f"If you didn't receive the prompt, it may have expired. "
        f"Reply with 'retry' to try again."
    )

    return {
        "text": message,
    }


def _retry_with_same_number() -> dict:
    app_logger.info("Retrying payment with same number")

    message = "🔄 Let's try that again. Sending a new payment request..."

    return {
        "text": message,
        "transition_to": ConversationState.PAYMENT_INITIATED,
    }


def _retry_with_different_number() -> dict:
    app_logger.info("Retrying payment with different number")

    message = (
        "📱 Let's use a different M-Pesa number.\n\n"
        "Please provide your Safaricom M-Pesa number:"
    )

    return {
        "text": message,
        "update_context": {
            "mpesa_phone_number": None,  # Clear previous number
            "mpesa_validation_attempts": 0,  # Reset attempts
        },
        "transition_to": ConversationState.PAYMENT_INITIATED,
    }


class PaymentPendingHandler(BaseStateHandler):
    """Handler for payment pending state - passive state waiting for callback."""

    def __init__(self, booking_repository: BookingRepository):
        self.booking_repo = booking_repository

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.info(
            "Handling PAYMENT_PENDING state",
            session_id=session.id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        context = session.context or {}

        # Handle retry/cancel actions from buttons
        if message_content == "retry_same_number":
            app_logger.info(
                "User wants to retry with same number",
                session_id=session.id,
            )
            return _retry_with_same_number()

        if message_content == "retry_different_number":
            app_logger.info(
                "User wants to retry with different number",
                session_id=session.id,
            )
            return _retry_with_different_number()

        if message_content == "cancel_payment":
            app_logger.info(
                "User wants to cancel payment",
                session_id=session.id,
            )
            return self._cancel_payment(context, customer_name)

        # Get booking and check payment status
        booking_id = context.get("booking_id")

        if not booking_id:
            app_logger.error(
                "No booking_id in context",
                session_id=session.id,
            )
            return {
                "text": "I apologize, but I couldn't find your booking details. "
                "Please start again by typing 'book'.",
                "update_context": {},
                "transition_to": ConversationState.IDLE,
            }

        booking = self.booking_repo.get_by_id(booking_id)

        if not booking:
            app_logger.error(
                "Booking not found",
                session_id=session.id,
                booking_id=booking_id,
            )
            return {
                "text": "I apologize, but I couldn't find your booking. "
                "Please contact us for assistance:\n📞 +254 712 345 678",
                "update_context": {},
                "transition_to": ConversationState.IDLE,
            }

        # Route based on payment status
        payment_status = booking.payment_status

        app_logger.info(
            "Checking payment status",
            session_id=session.id,
            booking_id=booking_id,
            payment_status=payment_status.value,
        )

        if payment_status == PaymentStatus.PAID:
            return _handle_payment_success(booking, customer_name)
        elif payment_status == PaymentStatus.FAILED:
            return _handle_payment_failure(booking)
        else:  # PENDING
            return _handle_still_pending(booking)

    def _cancel_payment(
        self,
        context: dict,
        customer_name: str | None = None,
    ) -> dict:
        booking_id = context.get("booking_id")

        if booking_id:
            self.booking_repo.cancel_booking(booking_id)
            app_logger.info(
                "Booking cancelled by user",
                booking_id=booking_id,
            )

        greeting = f"{customer_name}" if customer_name else "there"

        message = (
            f"Your booking has been cancelled, {greeting}.\n\n"
            f"If you'd like to book again or need assistance, feel free to reach out:\n"
            f"📞 +254 712 345 678\n"
            f"📧 info@glowhavenbeauty.co.ke\n\n"
            f"What else can I help you with?"
        )

        return {
            "text": message,
            "update_context": {},
            "transition_to": ConversationState.IDLE,
        }
