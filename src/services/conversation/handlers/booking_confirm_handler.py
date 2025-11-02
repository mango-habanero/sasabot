"""Handler for booking confirmation state."""

from datetime import datetime
from decimal import Decimal

from src.configuration import app_logger
from src.data.entities import ConversationSession
from src.data.enums import ConversationState
from src.data.repositories import BookingRepository
from src.services.business import (
    ContextService,
    PricingService,
    PromotionService,
    calculate_balance,
    format_price_display,
    select_best_promotion,
)
from src.services.conversation.handlers.base import BaseStateHandler
from src.utilities.booking import generate_booking_reference


def _cancel_booking(customer_name: str | None = None) -> dict:
    app_logger.info("Booking cancelled, returning to IDLE")

    greeting = f"{customer_name}" if customer_name else "there"

    cancellation_text = (
        f"No problem, {greeting}! Your booking has been cancelled.\n\n"
        f"What else can I help you with today?"
    )

    return {
        "text": cancellation_text,
        "update_context": {},
        "transition_to": ConversationState.IDLE,
    }


def _show_summary(
    context: dict,
    business_id: int,
    context_service: ContextService,
    pricing_service: PricingService,
    promotion_service: PromotionService,
    customer_name: str | None = None,
) -> dict:
    app_logger.debug("Building booking summary", business_id=business_id)

    service = context.get("selected_service", {})
    service_name = service.get("name", "Unknown Service")
    service_id = service.get("id")
    service_price = Decimal(str(service.get("price", 0)))
    duration_minutes = service.get("duration_minutes", 0)

    datetime_display = context.get("selected_datetime_display", "")
    selected_date_str = context.get("selected_date", "")

    business = context_service.get_business(business_id)
    location = context_service.get_primary_location(business_id)

    best_promotion = None
    if selected_date_str and service_id:
        try:
            appointment_date = datetime.fromisoformat(selected_date_str).date()
            applicable_promotions = promotion_service.get_applicable_promotions(
                business_id, service_id, appointment_date
            )

            if applicable_promotions:
                best_promotion = select_best_promotion(
                    applicable_promotions, service_price
                )

                if best_promotion:
                    app_logger.info(
                        "Auto-applying best promotion",
                        business_id=business_id,
                        service_id=service_id,
                        promotion_id=best_promotion.id,
                        promotion_name=best_promotion.name,
                    )
        except Exception as e:
            app_logger.warning(
                "Failed to check promotions",
                business_id=business_id,
                service_id=service_id,
                error=str(e),
            )

    pricing = pricing_service.calculate_with_promotion(
        service_price, business_id, best_promotion
    )

    greeting = f"{customer_name}," if customer_name else "Here's"

    summary_text = (
        f"✨ **Booking Summary**\n\n"
        f"📋 **Service:** {service_name}\n"
        f"⏱️ **Duration:** {duration_minutes} mins\n\n"
        f"📅 **Date & Time:**\n{datetime_display}\n\n"
        f"💰 **Pricing:**\n"
    )

    if pricing["promotion_applied"]:
        summary_text += (
            f"• Original Price: {format_price_display(pricing['original_price'])}\n"
            f"🎉 Discount ({pricing['promotion_applied']}): -{format_price_display(pricing['discount_amount'])}\n"
            f"• **Final Price: {format_price_display(pricing['final_price'])}**\n"
            f"• Deposit ({pricing['deposit_percentage']:.0f}%): {format_price_display(pricing['deposit_amount'])}\n"
            f"• Balance on visit: {format_price_display(pricing['balance_amount'])}\n\n"
        )
    else:
        summary_text += (
            f"• Total: {format_price_display(pricing['final_price'])}\n"
            f"• Deposit ({pricing['deposit_percentage']:.0f}%): {format_price_display(pricing['deposit_amount'])}\n"
            f"• Balance on visit: {format_price_display(pricing['balance_amount'])}\n\n"
        )

    summary_text += (
        f"📍 **Location:**\n{business.name}\n"
        f"{location.address}\n\n"
        f"{greeting} please confirm your booking to proceed with payment."
    )

    app_logger.info(
        "Booking summary prepared",
        business_id=business_id,
        service_id=service_id,
        service_name=service_name,
        original_price=float(pricing["original_price"]),
        final_price=float(pricing["final_price"]),
        discount=float(pricing["discount_amount"]),
        deposit_amount=float(pricing["deposit_amount"]),
        has_promotion=bool(pricing["promotion_applied"]),
    )

    footer_text = f"{pricing['deposit_percentage']:.0f}% deposit required"
    if pricing["promotion_applied"]:
        footer_text = f"🎉 Promo applied • {footer_text}"

    return {
        "buttons": {
            "body": summary_text,
            "buttons": [
                ("confirm_booking", "✅ Confirm Booking"),
                ("cancel_booking", "❌ Cancel"),
            ],
            "footer": footer_text,
        },
        "update_context": {
            "promotion_id": best_promotion.id if best_promotion else None,
            "promotion_name": pricing["promotion_applied"],
            "discount_amount": float(pricing["discount_amount"]),
        },
    }


class BookingConfirmHandler(BaseStateHandler):
    def __init__(
        self,
        booking_repository: BookingRepository,
        context_service: ContextService,
        pricing_service: PricingService,
        promotion_service: PromotionService,
    ):
        self.booking_repo = booking_repository
        self.context_service = context_service
        self.pricing_service = pricing_service
        self.promotion_service = promotion_service

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        business_id = session.business_id

        app_logger.info(
            "Handling BOOKING_CONFIRM state",
            session_id=session.id,
            business_id=business_id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        context = session.context or {}

        if message_content == "confirm_booking":
            app_logger.info(
                "Booking confirmed by user",
                session_id=session.id,
                business_id=business_id,
                phone_number=session.phone_number,
            )
            return self._create_booking_and_proceed(
                session, business_id, context, customer_name
            )

        if message_content == "cancel_booking":
            app_logger.info(
                "Booking cancelled by user",
                session_id=session.id,
                business_id=business_id,
                phone_number=session.phone_number,
            )
            return _cancel_booking(customer_name)

        app_logger.info(
            "Showing booking summary",
            session_id=session.id,
            business_id=business_id,
        )
        return _show_summary(
            context,
            business_id,
            self.context_service,
            self.pricing_service,
            self.promotion_service,
            customer_name,
        )

    def _create_booking_and_proceed(
        self,
        session: ConversationSession,
        business_id: int,
        context: dict,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.debug(
            "Creating booking record",
            session_id=session.id,
            business_id=business_id,
        )

        service = context.get("selected_service", {})
        service_id = service.get("id")
        service_name = service.get("name")
        service_price = Decimal(str(service.get("price", 0)))
        duration_minutes = service.get("duration_minutes", 0)
        category_id = service.get("category_id")

        promotion_id = context.get("promotion_id")
        discount_amount = Decimal(str(context.get("discount_amount", 0)))

        selected_date = context.get("selected_date")
        selected_time = context.get("selected_time")
        datetime_display = context.get("selected_datetime_display")

        if not all([service_id, selected_date, selected_time]):
            app_logger.error(
                "Missing required booking data in context",
                session_id=session.id,
                business_id=business_id,
                context=context,
            )
            return {
                "text": "Something went wrong. Please start the booking process again.",
                "transition_to": ConversationState.IDLE,
            }

        category = self.context_service.get_categories(business_id)
        category_obj = next((c for c in category if c.id == category_id), None)
        category_name = category_obj.name if category_obj else "Unknown"

        appointment_date = datetime.fromisoformat(selected_date).date()
        appointment_time = datetime.strptime(selected_time, "%H:%M").time()

        final_price = service_price - discount_amount
        deposit_amount = self.pricing_service.calculate_deposit(
            final_price, business_id
        )
        balance_amount = calculate_balance(final_price, deposit_amount)

        booking_reference = generate_booking_reference()

        booking = self.booking_repo.create(
            business_id=business_id,
            service_id=service_id,
            booking_reference=booking_reference,
            customer_phone=session.phone_number,
            customer_name=customer_name,
            service_category=category_name,
            service_name=service_name,
            service_duration=f"{duration_minutes} mins",
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_datetime_display=datetime_display,
            service_price=final_price,
            deposit_amount=deposit_amount,
            balance_amount=balance_amount,
            total_amount=final_price,
            conversation_session_id=session.id,
        )

        if not booking:
            app_logger.error(
                "Failed to create booking",
                session_id=session.id,
                business_id=business_id,
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
            business_id=business_id,
            booking_reference=booking_reference,
            customer_phone=session.phone_number,
            promotion_applied=bool(promotion_id),
        )

        greeting = f"Perfect, {customer_name}!" if customer_name else "Perfect!"

        confirmation_text = (
            f"{greeting}\n\n"
            f"✅ Your booking has been created!\n\n"
            f"📋 **Booking Reference:** {booking_reference}\n"
        )

        if discount_amount > 0:
            promotion_name = context.get("promotion_name", "Promotion")
            confirmation_text += (
                f"🎉 **{promotion_name} Applied!**\n"
                f"You saved {format_price_display(discount_amount)}!\n\n"
            )

        confirmation_text += (
            f"💳 **Deposit Amount:** {format_price_display(deposit_amount)}\n\n"
            f"Next, I'll send you an M-Pesa payment request for the deposit. "
            f"Please check your phone and enter your M-Pesa PIN to complete the payment."
        )

        return {
            "text": confirmation_text,
            "update_context": {
                "booking_id": booking.id,
                "booking_reference": booking_reference,
                "deposit_amount": float(deposit_amount),
                "balance_amount": float(balance_amount),
                "total_amount": float(final_price),
            },
            "transition_to": ConversationState.PAYMENT_INITIATED,
        }
