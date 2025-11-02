"""Handler for IDLE state - waiting for user input."""

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.data.enums.intent import IntentType
from src.services.business import ContextService
from src.services.conversation.handlers.base import BaseStateHandler
from src.services.llm.intent_service import IntentRecognitionService
from src.utilities import (
    format_complete_context,
    format_operating_hours,
    format_promotions,
)


def _handle_low_confidence(customer_name: str | None) -> dict:
    greeting = f"{customer_name}" if customer_name else "there"
    return {
        "text": f"Hi {greeting}! I'd love to help, but I'm not quite sure what you're asking. "
        f"Could you rephrase that? I can help you:\n"
        f"• Book an appointment\n"
        f"• Check service prices\n"
        f"• Learn about our location and hours\n"
        f"• View current promotions"
    }


def _handle_booking_intent(customer_name: str | None) -> dict:
    greeting = f"Great, {customer_name}!" if customer_name else "Great!"
    return {
        "text": f"{greeting} Let's book your appointment. "
        f"I'll show you our available services next.",
        "transition_to": ConversationState.BOOKING_SELECT_SERVICE,
    }


def _handle_general_inquiry(
    intent,
    customer_name: str | None,
    business_id: int,
    context_service: ContextService,
) -> dict:
    message_lower = intent.reasoning.lower() if intent.reasoning else ""

    if any(word in message_lower for word in ["hour", "open", "time", "when"]):
        location = context_service.get_primary_location(business_id)
        hours_formatted = format_operating_hours(location.operating_hours)
        return {
            "text": f"We're open every day! 🕐\n\n"
            f"**Operating Hours:**\n"
            f"{hours_formatted}\n\n"
            f"We're here to serve you 7 days a week!"
        }

    if any(word in message_lower for word in ["location", "where", "address", "find"]):
        business = context_service.get_business(business_id)
        location = context_service.get_primary_location(business_id)

        contact_lines = [
            f"📍 **Our Location:**\n{location.address}\n",
            "\n**Contact Us:**",
        ]

        if business.phone:
            contact_lines.append(f"📞 {business.phone}")
        if business.email:
            contact_lines.append(f"📧 {business.email}")
        if business.instagram_handle:
            contact_lines.append(f"📱 Instagram: @{business.instagram_handle}")

        return {"text": "\n".join(contact_lines)}

    if any(
        word in message_lower
        for word in ["promo", "deal", "discount", "offer", "special"]
    ):
        promotions = context_service.get_active_promotions(business_id)
        if not promotions:
            return {
                "text": "We don't have any active promotions at the moment. Check back soon!"
            }

        promo_text = format_promotions(promotions)
        return {"text": f"🎉 {promo_text}"}

    if any(word in message_lower for word in ["service", "what do you", "offer"]):
        categories = context_service.get_categories(business_id)
        services = context_service.get_all_services(business_id)

        if not services:
            return {"text": "We're updating our services. Please check back soon!"}

        services_text = "✨ **Our Services:**\n\n"
        for category in categories:
            services_text += f"• {category.name}\n"

        prices = [service.price for service in services]
        min_price = min(prices)
        max_price = max(prices)

        services_text += (
            f"\n💰 Prices range from KES {min_price:,.2f} - {max_price:,.2f}\n"
            f"Would you like to see specific service prices or book an appointment?"
        )
        return {"text": services_text}

    greeting = f"Hi {customer_name}!" if customer_name else "Hello!"
    business = context_service.get_business(business_id)
    return {
        "text": f"{greeting} Welcome to {business.name}! 🌟\n\n"
        f"I can help you with:\n"
        f"• Booking appointments\n"
        f"• Viewing our services and prices\n"
        f"• Checking our location and hours\n"
        f"• Learning about current promotions\n\n"
        f"What would you like to know?"
    }


def _handle_price_check(
    intent, business_id: int, context_service: ContextService
) -> dict:
    entities = intent.entities or {}
    service_category = entities.get("service_category", "").lower()

    categories = context_service.get_categories(business_id)
    all_services = context_service.get_all_services(business_id)

    if service_category:
        for category in categories:
            if service_category in category.name.lower():
                category_services = [
                    s for s in all_services if s.category_id == category.id
                ]
                if not category_services:
                    continue

                price_text = f"💰 **{category.name} Prices:**\n\n"
                for service in category_services:
                    price_text += (
                        f"• {service.name}: KES {service.price:,.2f} "
                        f"({service.duration_minutes} mins)\n"
                    )
                price_text += "\nWould you like to book any of these services?"
                return {"text": price_text}

    price_text = "💰 **Our Service Prices:**\n\n"
    for category in categories:
        category_services = [s for s in all_services if s.category_id == category.id]
        if not category_services:
            continue

        price_text += f"**{category.name}:**\n"
        for service in category_services:
            price_text += (
                f"• {service.name}: KES {service.price:,.2f} "
                f"({service.duration_minutes} mins)\n"
            )
        price_text += "\n"

    price_text += "Ready to book? Just let me know! 💅"
    return {"text": price_text}


def _handle_feedback_intent(customer_name: str | None) -> dict:
    greeting = f"Thank you, {customer_name}!" if customer_name else "Thank you!"
    return {
        "text": f"{greeting} We value your feedback. "
        f"Let me help you share your experience with us.",
        "transition_to": ConversationState.FEEDBACK_RATING,
    }


def _handle_payment_inquiry(business_id: int, context_service: ContextService) -> dict:
    config = context_service.get_configuration(business_id)

    payment_methods = config.accepted_payment_methods
    methods_text = "\n".join([f"• {method.title()}" for method in payment_methods])

    return {
        "text": f"💳 **Payment Information:**\n\n"
        f"We accept the following payment methods:\n"
        f"{methods_text}\n\n"
        f"**Booking Policy:**\n"
        f"A {config.deposit_percentage:.0f}% deposit is required to confirm your appointment. "
        f"You can pay the deposit via M-Pesa when booking.\n\n"
        f"Would you like to book an appointment?"
    }


def _handle_unknown_intent(customer_name: str | None) -> dict:
    greeting = f"{customer_name}" if customer_name else "there"
    return {
        "text": f"Hi {greeting}! I'm not sure I understood that. "
        f"I'm here to help you with:\n\n"
        f"• **Booking** appointments\n"
        f"• Checking **prices** for our services\n"
        f"• **Location** and operating hours\n"
        f"• Current **promotions**\n"
        f"• Providing **feedback**\n\n"
        f"What would you like to do?"
    }


class IdleStateHandler(BaseStateHandler):
    def __init__(self, context_service: ContextService):
        self.context_service = context_service
        self.intent_service = IntentRecognitionService()

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        business_id = session.business_id

        app_logger.info(
            "Handling IDLE state with intent recognition",
            session_id=session.id,
            business_id=business_id,
            phone_number=session.phone_number,
            message_preview=message_content[:50],
        )

        # Get business context for LLM
        business = self.context_service.get_business(business_id)
        location = self.context_service.get_primary_location(business_id)
        categories = self.context_service.get_categories(business_id)
        services = self.context_service.get_all_services(business_id)
        promotions = self.context_service.get_active_promotions(business_id)

        business_context = format_complete_context(
            business, location, categories, services, promotions
        )

        # Recognize intent with business context
        intent = await self.intent_service.recognize_intent(
            message_content,
            business_context=business_context,
        )

        app_logger.info(
            "Intent recognized in IDLE handler",
            session_id=session.id,
            intent_type=intent.type.value,
            confidence=intent.confidence,
        )

        if intent.confidence < 0.7:
            return _handle_low_confidence(customer_name)

        if intent.type == IntentType.BOOK_APPOINTMENT:
            return _handle_booking_intent(customer_name)

        elif intent.type == IntentType.GENERAL_INQUIRY:
            return _handle_general_inquiry(
                intent, customer_name, business_id, self.context_service
            )

        elif intent.type == IntentType.PRICE_CHECK:
            return _handle_price_check(intent, business_id, self.context_service)

        elif intent.type == IntentType.FEEDBACK:
            return _handle_feedback_intent(customer_name)

        elif intent.type == IntentType.PAYMENT_RELATED:
            return _handle_payment_inquiry(business_id, self.context_service)

        else:
            return _handle_unknown_intent(customer_name)
