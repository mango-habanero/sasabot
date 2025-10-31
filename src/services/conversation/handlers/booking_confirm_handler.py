"""Handler for BOOKING_CONFIRM state."""

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.data.repositories.booking import BookingRepository
from src.services.conversation.handlers.base import BaseStateHandler
from src.utilities import calculate_deposit, generate_booking_reference


def _cancel_booking(customer_name: str | None = None) -> dict:
    app_logger.info("Booking cancelled, returning to IDLE")

    greeting = f"{customer_name}" if customer_name else "there"

    cancellation_text = (
        f"No problem, {greeting}! Your booking has been cancelled.\n\n"
        f"What else can I help you with today?"
    )

    return {
        "text": cancellation_text,
        "update_context": {},  # Clear context by setting empty dict
        "transition_to": ConversationState.IDLE,
    }


def _show_summary(
    context: dict,
    customer_name: str | None = None,
) -> dict:
    """
    Show booking summary with confirmation buttons.

    :param context: Session context with booking details
    :param customer_name: Customer name (optional)
    :return: Response dict with buttons message
    """
    app_logger.debug("Building booking summary")

    # Extract booking details from context
    service = context.get("selected_service", {})
    service_name = service.get("name", "Unknown Service")
    service_category = service.get("category", "")
    service_price = service.get("price", 0)
    service_duration = service.get("duration", "")

    datetime_display = context.get("selected_datetime_display", "")

    # Calculate deposit
    financial = calculate_deposit(service_price)

    # Build summary message
    greeting = f"{customer_name}," if customer_name else "Here's"

    summary_text = (
        f"✨ **Booking Summary**\n\n"
        f"📋 **Service:** {service_name}\n"
        f"🏷️ **Category:** {service_category}\n"
        f"⏱️ **Duration:** {service_duration}\n\n"
        f"📅 **Date & Time:**\n{datetime_display}\n\n"
        f"💰 **Pricing:**\n"
        f"• Total: KES {financial['total_amount']:,}\n"
        f"• Deposit (30%): KES {financial['deposit_amount']:,}\n"
        f"• Balance on visit: KES {financial['balance_amount']:,}\n\n"
        f"📍 **Location:**\nGlow Haven Beauty Lounge\n"
        f"1st Floor, Valley Arcade Mall, Nairobi\n\n"
        f"{greeting} please confirm your booking to proceed with payment."
    )

    app_logger.info(
        "Booking summary prepared",
        service_name=service_name,
        total_amount=financial["total_amount"],
        deposit_amount=financial["deposit_amount"],
    )

    return {
        "buttons": {
            "body": summary_text,
            "buttons": [
                ("confirm_booking", "✅ Confirm Booking"),
                ("cancel_booking", "❌ Cancel"),
            ],
            "footer": "30% deposit required to confirm",
        }
    }


class BookingConfirmHandler(BaseStateHandler):
    """Handler for booking confirmation with summary display."""

    def __init__(self, booking_repository: BookingRepository):
        """
        Initialize handler with booking repository.

        :param booking_repository: Repository for booking operations
        :type booking_repository: BookingRepository
        """
        self.booking_repo = booking_repository

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.info(
            "Handling BOOKING_CONFIRM state",
            session_id=session.id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        context = session.context or {}

        # Route based on message content

        # Scenario A: User confirmed booking
        if message_content == "confirm_booking":
            app_logger.info(
                "Booking confirmed by user",
                session_id=session.id,
                phone_number=session.phone_number,
            )
            return self._create_booking_and_proceed(session, context, customer_name)

        # Scenario B: User cancelled booking
        if message_content == "cancel_booking":
            app_logger.info(
                "Booking cancelled by user",
                session_id=session.id,
                phone_number=session.phone_number,
            )
            return _cancel_booking(customer_name)

        # Scenario C: First entry - show summary with confirmation buttons
        app_logger.info(
            "Showing booking summary",
            session_id=session.id,
        )
        return _show_summary(context, customer_name)

    def _create_booking_and_proceed(
        self,
        session: ConversationSession,
        context: dict,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.debug("Creating booking record", session_id=session.id)

        # Extract booking details from context
        service = context.get("selected_service", {})
        selected_date = context.get("selected_date")
        selected_time = context.get("selected_time")
        datetime_display = context.get("selected_datetime_display")

        # Parse date and time strings
        from datetime import datetime

        appointment_date = datetime.fromisoformat(selected_date).date()
        appointment_time = datetime.strptime(selected_time, "%H:%M").time()

        # Calculate financial details
        service_price = service.get("price", 0)
        financial = calculate_deposit(service_price)

        # Generate booking reference
        booking_reference = generate_booking_reference()

        # Create booking record
        booking_data = {
            "booking_reference": booking_reference,
            "customer_phone": session.phone_number,
            "customer_name": customer_name,
            "service_category": service.get("category"),
            "service_name": service.get("name"),
            "service_duration": service.get("duration"),
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "appointment_datetime_display": datetime_display,
            "service_price": service_price,
            "deposit_amount": financial["deposit_amount"],
            "balance_amount": financial["balance_amount"],
            "total_amount": financial["total_amount"],
            "conversation_session_id": session.id,
        }

        booking = self.booking_repo.create(booking_data)

        if not booking:
            app_logger.error(
                "Failed to create booking",
                session_id=session.id,
                booking_reference=booking_reference,
            )
            return {
                "text": "I apologize, but something went wrong while creating your booking. "
                "Please try again or contact us directly.",
                "transition_to": ConversationState.IDLE,
            }

        app_logger.info(
            "Booking created successfully",
            booking_id=booking.id,
            booking_reference=booking_reference,
            customer_phone=session.phone_number,
        )

        # Prepare confirmation message
        greeting = f"Perfect, {customer_name}!" if customer_name else "Perfect!"

        confirmation_text = (
            f"{greeting}\n\n"
            f"✅ Your booking has been created!\n\n"
            f"📋 **Booking Reference:** {booking_reference}\n"
            f"💳 **Deposit Amount:** KES {financial['deposit_amount']:,}\n\n"
            f"Next, I'll send you an M-Pesa payment request for the deposit. "
            f"Please check your phone and enter your M-Pesa PIN to complete the payment."
        )

        return {
            "text": confirmation_text,
            "update_context": {
                "booking_id": booking.id,
                "booking_reference": booking_reference,
                "deposit_amount": financial["deposit_amount"],
                "balance_amount": financial["balance_amount"],
                "total_amount": financial["total_amount"],
            },
            "transition_to": ConversationState.PAYMENT_INITIATED,
        }
