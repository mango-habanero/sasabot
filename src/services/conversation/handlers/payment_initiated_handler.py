"""Handler for PAYMENT_INITIATED state."""

from src.configuration import app_logger, settings
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.data.repositories.booking import BookingRepository
from src.services.conversation.handlers.base import BaseStateHandler
from src.services.payment.safaricom import DarajaClient
from src.utilities import is_safaricom_number, normalize_phone_number

MAX_MPESA_VALIDATION_ATTEMPTS = 2


class PaymentInitiatedHandler(BaseStateHandler):
    """Handler for payment initiation with M-Pesa validation."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        daraja_client: DarajaClient,
    ):
        self.booking_repo = booking_repository
        self.daraja_client = daraja_client

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.info(
            "Handling PAYMENT_INITIATED state",
            session_id=session.id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        context = session.context or {}

        # Scenario A: First entry - check customer phone
        if "mpesa_validation_attempts" not in context:
            return await self._check_customer_phone(session, context, customer_name)

        # Scenario B: User is providing M-Pesa number
        return await self._validate_and_initiate_payment(
            session, context, message_content, customer_name
        )

    async def _check_customer_phone(
        self,
        session: ConversationSession,
        context: dict,
        customer_name: str | None = None,
    ) -> dict:
        customer_phone = session.phone_number

        app_logger.info(
            "Checking if customer phone is Safaricom",
            session_id=session.id,
            customer_phone=customer_phone,
        )

        if is_safaricom_number(customer_phone):
            # Customer phone is Safaricom - proceed with STK push
            app_logger.info(
                "Customer phone is Safaricom, initiating STK push",
                session_id=session.id,
            )
            return await self._initiate_stk_push(session, context, customer_phone)

        # Customer phone is NOT Safaricom - ask for M-Pesa number
        app_logger.info(
            "Customer phone is not Safaricom, requesting M-Pesa number",
            session_id=session.id,
        )

        greeting = f"{customer_name}" if customer_name else "there"

        message = (
            f"Hi {greeting}!\n\n"
            f"❌ Your number ({customer_phone}) is not registered with Safaricom M-Pesa.\n\n"
            f"To complete your booking payment, please provide a valid Safaricom M-Pesa number.\n\n"
            f"Simply reply with the phone number (e.g., 0722123456 or +254722123456):"
        )

        return {
            "text": message,
            "update_context": {
                "mpesa_validation_attempts": 0,
            },
        }

    async def _validate_and_initiate_payment(
        self,
        session: ConversationSession,
        context: dict,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        attempts = context.get("mpesa_validation_attempts", 0)

        app_logger.info(
            "Validating M-Pesa number",
            session_id=session.id,
            attempt=attempts + 1,
            max_attempts=MAX_MPESA_VALIDATION_ATTEMPTS,
        )

        # Try to normalize and validate phone number
        try:
            mpesa_phone = normalize_phone_number(message_content)

            if is_safaricom_number(mpesa_phone):
                # Valid Safaricom number - proceed with STK push
                app_logger.info(
                    "Valid M-Pesa number provided",
                    session_id=session.id,
                    mpesa_phone=mpesa_phone,
                )

                # Store M-Pesa number in context
                context["mpesa_phone_number"] = mpesa_phone

                return await self._initiate_stk_push(session, context, mpesa_phone)

        except ValueError as e:
            app_logger.warning(
                "Invalid phone number format",
                session_id=session.id,
                message_content=message_content,
                error=str(e),
            )

        # Invalid number - increment attempts and handle retry or cancel
        attempts += 1

        if attempts >= MAX_MPESA_VALIDATION_ATTEMPTS:
            # Max attempts reached - cancel booking
            app_logger.warning(
                "Max M-Pesa validation attempts reached, cancelling booking",
                session_id=session.id,
                attempts=attempts,
            )

            return await self._cancel_booking_due_to_validation_failure(
                context, customer_name
            )

        # Still have attempts left - ask again
        app_logger.info(
            "Invalid M-Pesa number, asking again",
            session_id=session.id,
            attempts=attempts,
            remaining_attempts=MAX_MPESA_VALIDATION_ATTEMPTS - attempts,
        )

        message = (
            f"❌ Invalid M-Pesa number.\n\n"
            f"Please provide a valid Safaricom number starting with:\n"
            f"• 07XX (e.g., 0722123456)\n"
            f"• 011X (e.g., 0110123456)\n\n"
            f"Attempt {attempts} of {MAX_MPESA_VALIDATION_ATTEMPTS}. Please try again:"
        )

        return {
            "text": message,
            "update_context": {
                "mpesa_validation_attempts": attempts,
            },
        }

    async def _initiate_stk_push(
        self,
        session: ConversationSession,
        context: dict,
        payment_phone: str,
    ) -> dict:
        booking_id = context.get("booking_id")
        booking_reference = context.get("booking_reference")
        deposit_amount = context.get("deposit_amount")

        if not all([booking_id, booking_reference, deposit_amount]):
            app_logger.error(
                "Missing booking details in context",
                session_id=session.id,
                context=context,
            )
            return {
                "text": "I apologize, but something went wrong. "
                "Please start your booking again by typing 'book'.",
                "update_context": {},
                "transition_to": ConversationState.IDLE,
            }

        # Get booking from database
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            app_logger.error(
                "Booking not found",
                session_id=session.id,
                booking_id=booking_id,
            )
            return {
                "text": "I apologize, but I couldn't find your booking. "
                "Please start again by typing 'book'.",
                "update_context": {},
                "transition_to": ConversationState.IDLE,
            }

        # Prepare STK push parameters
        account_reference = booking_reference
        transaction_desc = f"Deposit for {booking.service_name}"
        callback_url = settings.DARAJA_CALLBACK_URL

        app_logger.info(
            "Initiating STK push",
            booking_id=booking_id,
            booking_reference=booking_reference,
            amount=deposit_amount,
            payment_phone=payment_phone,
        )

        try:
            # Initiate STK push
            stk_response = await self.daraja_client.initiate_stk_push(
                customer_phone=payment_phone,
                amount=deposit_amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                callback_url=callback_url,
            )

            # Update booking with CheckoutRequestID
            booking.mpesa_checkout_request_id = stk_response.checkout_request_id
            self.booking_repo.session.commit()

            app_logger.info(
                "STK push initiated successfully",
                booking_id=booking_id,
                checkout_request_id=stk_response.checkout_request_id,
            )

            # Show success message
            message = (
                f"📱 **Payment Request Sent!**\n\n"
                f"Please check your phone for an M-Pesa payment prompt.\n\n"
                f"💰 Amount: KES {deposit_amount:,}\n"
                f"📋 Reference: {booking_reference}\n\n"
                f"Enter your M-Pesa PIN to complete the payment.\n\n"
                f"⏱️ The prompt will expire in 60 seconds."
            )

            return {
                "text": message,
                "transition_to": ConversationState.PAYMENT_PENDING,
            }

        except Exception as e:
            app_logger.error(
                "Failed to initiate STK push",
                booking_id=booking_id,
                error=str(e),
            )

            return {
                "text": "I apologize, but we couldn't send the payment request. "
                "Please try again or contact us directly:\n"
                "📞 +254 712 345 678",
                "transition_to": ConversationState.IDLE,
            }

    async def _cancel_booking_due_to_validation_failure(
        self,
        context: dict,
        customer_name: str | None = None,
    ) -> dict:
        booking_id = context.get("booking_id")

        if booking_id:
            # Cancel the booking in database
            self.booking_repo.cancel_booking(booking_id)
            app_logger.info(
                "Booking cancelled due to validation failure",
                booking_id=booking_id,
            )

        greeting = f"{customer_name}" if customer_name else "there"

        message = (
            f"Sorry {greeting}, we couldn't verify a valid M-Pesa number.\n\n"
            f"Your booking has been cancelled.\n\n"
            f"If you'd like to try again, please start a new booking "
            f"or contact us directly:\n"
            f"📞 +254 712 345 678\n"
            f"📧 info@glowhavenbeauty.co.ke"
        )

        return {
            "text": message,
            "update_context": {},
            "transition_to": ConversationState.IDLE,
        }
