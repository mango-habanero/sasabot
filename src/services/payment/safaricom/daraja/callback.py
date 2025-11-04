"""Service for processing Daraja payment callbacks."""

from src.configuration import app_logger, settings
from src.data.dtos.responses.daraja import DarajaCallbackPayload
from src.data.entities import Booking
from src.data.enums import PaymentStatus
from src.data.repositories.booking import BookingRepository
from src.services.notification.whatsapp.client import WhatsAppClient
from src.services.reports import ReceiptPDFGenerator


class DarajaCallbackService:
    """Service for processing M-Pesa payment callbacks."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        whatsapp_client: WhatsAppClient,
    ):
        self.booking_repo = booking_repository
        self.whatsapp_client = whatsapp_client

    async def process_callback(self, payload: DarajaCallbackPayload) -> bool:
        checkout_request_id = payload.body.stk_callback.checkout_request_id
        result_code = payload.body.stk_callback.result_code
        result_desc = payload.body.stk_callback.result_desc

        app_logger.info(
            "Processing Daraja callback",
            checkout_request_id=checkout_request_id,
            result_code=result_code,
            result_desc=result_desc,
        )

        # find booking by CheckoutRequestID
        booking = self.booking_repo.get_by_checkout_request_id(checkout_request_id)

        if not booking:
            app_logger.error(
                "Booking not found for callback",
                checkout_request_id=checkout_request_id,
            )
            # Don't block Daraja - return success
            return True

        # Process based on result code
        if payload.is_successful():
            await self._handle_success(payload, booking)
        else:
            await self._handle_failure(payload, booking)

        return True

    async def _handle_success(
        self,
        payload: DarajaCallbackPayload,
        booking: Booking,
    ) -> None:
        assert booking.id is not None, "Booking ID must exist for database record"

        receipt_number = payload.get_receipt_number()
        amount = payload.get_amount()

        app_logger.info(
            "Payment successful",
            booking_id=booking.id,
            booking_reference=booking.booking_reference,
            receipt_number=receipt_number,
            amount=amount,
        )

        # Update booking payment status
        self.booking_repo.update_payment_status(
            booking_id=booking.id,
            status=PaymentStatus.PAID,
            receipt_number=receipt_number,
        )

        await self._send_receipt_pdf(booking, receipt_number or "N/A")

    async def _handle_failure(
        self,
        payload: DarajaCallbackPayload,
        booking: Booking,
    ) -> None:
        assert booking.id is not None, "Booking ID must exist for database record"

        result_desc = payload.body.stk_callback.result_desc

        app_logger.warning(
            "Payment failed",
            booking_id=booking.id,
            booking_reference=booking.booking_reference,
            result_code=payload.body.stk_callback.result_code,
            result_desc=result_desc,
        )

        # Update booking payment status
        self.booking_repo.update_payment_status(
            booking_id=booking.id,
            status=PaymentStatus.FAILED,
        )

        # Send WhatsApp notification
        await self._notify_payment_failure(booking, result_desc)

    async def _notify_payment_failure(
        self,
        booking: Booking,
        result_desc: str,
    ) -> None:
        message = (
            f"❌ **Payment Failed**\n\n"
            f"Your payment could not be processed.\n\n"
            f"📋 **Booking Reference:** {booking.booking_reference}\n"
            f"❗ **Reason:** {result_desc}\n\n"
            f"Please try booking again or contact us for assistance:\n"
            f"📞 +254 712 345 678\n"
            f"📧 info@glowhavenbeauty.co.ke"
        )

        try:
            await self.whatsapp_client.send_text(
                to=booking.customer_phone,
                text=message,
            )
            app_logger.info(
                "Payment failure notification sent",
                booking_id=booking.id,
                customer_phone=booking.customer_phone,
            )
        except Exception as e:
            app_logger.error(
                "Failed to send payment failure notification",
                booking_id=booking.id,
                error=str(e),
            )

    async def _notify_payment_success(
        self,
        booking: Booking,
        receipt_number: str,
    ) -> None:
        message = (
            f"✅ **Payment Successful!**\n\n"
            f"Your deposit has been received.\n\n"
            f"📋 **Booking Reference:** {booking.booking_reference}\n"
            f"💳 **M-Pesa Receipt:** {receipt_number}\n"
            f"💰 **Amount Paid:** KES {booking.deposit_amount:,}\n\n"
            f"📅 **Appointment Details:**\n"
            f"• Service: {booking.service_name}\n"
            f"• Date & Time: {booking.appointment_datetime_display}\n"
            f"• Balance on visit: KES {booking.balance_amount:,}\n\n"
            f"📍 **Location:**\n"
            f"Glow Haven Beauty Lounge\n"
            f"1st Floor, Valley Arcade Mall, Nairobi\n\n"
            f"We look forward to seeing you! 💅✨"
        )

        try:
            await self.whatsapp_client.send_text(
                to=booking.customer_phone,
                text=message,
            )
            app_logger.info(
                "Payment success notification sent",
                booking_id=booking.id,
                customer_phone=booking.customer_phone,
            )
        except Exception as e:
            app_logger.error(
                "Failed to send payment success notification",
                booking_id=booking.id,
                error=str(e),
            )

    async def _notify_payment_success_fallback(
        self,
        booking: Booking,
        receipt_number: str,
    ) -> None:
        message = (
            f"✅ **Payment Successful!**\n\n"
            f"Your deposit has been received.\n\n"
            f"📋 **Booking Reference:** {booking.booking_reference}\n"
            f"💳 **M-Pesa Receipt:** {receipt_number}\n"
            f"💰 **Amount Paid:** KES {booking.deposit_amount:,}\n\n"
            f"📅 **Appointment Details:**\n"
            f"• Service: {booking.service_name}\n"
            f"• Date & Time: {booking.appointment_datetime_display}\n"
            f"• Balance on visit: KES {booking.balance_amount:,}\n\n"
            f"📍 **Location:**\n"
            f"Glow Haven Beauty Lounge\n"
            f"1st Floor, Valley Arcade Mall, Nairobi\n\n"
            f"We look forward to seeing you! 💅✨"
        )

        try:
            await self.whatsapp_client.send_text(
                to=booking.customer_phone,
                text=message,
            )
            app_logger.info(
                "Fallback payment success notification sent",
                booking_id=booking.id,
            )
        except Exception as e:
            app_logger.error(
                "Failed to send fallback notification",
                booking_id=booking.id,
                error=str(e),
            )

    async def _send_receipt_pdf(
        self,
        booking: Booking,
        receipt_number: str,
    ) -> None:
        try:
            pdf_generator = ReceiptPDFGenerator()
            pdf_path = pdf_generator.generate(booking)

            receipt_url = f"{settings.BASE_URL}{settings.API_PREFIX}/reports/receipts/{pdf_path.name}"

            app_logger.info(
                "Sending PDF receipt",
                booking_id=booking.id,
                receipt_url=receipt_url,
            )

            await self.whatsapp_client.send_document(
                to=booking.customer_phone,
                document_url=receipt_url,
                filename=f"Glow_Haven_Receipt_{booking.booking_reference}.pdf",
                caption=(
                    f"✅ Payment Successful!\n\n"
                    f"Your deposit of KES {booking.deposit_amount:,} has been received.\n"
                    f"M-Pesa Receipt: {receipt_number}\n\n"
                    f"📋 Booking Reference: {booking.booking_reference}\n"
                    f"📅 Appointment: {booking.appointment_datetime_display}\n"
                    f"💰 Balance on visit: KES {booking.balance_amount:,}\n\n"
                    f"See you soon! 💅✨"
                ),
            )

            app_logger.info(
                "PDF receipt sent successfully",
                booking_id=booking.id,
                customer_phone=booking.customer_phone,
            )

        except Exception as e:
            app_logger.error(
                "Failed to send PDF receipt",
                booking_id=booking.id,
                error=str(e),
            )

            await self._notify_payment_success_fallback(booking, receipt_number)
