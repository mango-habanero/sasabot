"""Handler for IDLE state - waiting for user input."""

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.data.enums.intent import IntentType
from src.services.conversation.handlers.base import BaseStateHandler
from src.services.llm.business_context import (
    PROMOTIONS,
    SERVICES,
)
from src.services.llm.intent_service import IntentRecognitionService


def _handle_low_confidence(customer_name: str | None) -> dict:
    """Handle a low-confidence intent recognition."""
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
    """Handle booking appointment intent."""
    greeting = f"Great, {customer_name}!" if customer_name else "Great!"
    return {
        "text": f"{greeting} Let's book your appointment. "
        f"I'll show you our available services next.",
        "transition_to": ConversationState.BOOKING_SELECT_SERVICE,
    }


def _handle_general_inquiry(intent, customer_name: str | None) -> dict:
    """Handle general inquiry - return pre-formatted responses."""

    # Check what type of general inquiry
    message_lower = intent.reasoning.lower() if intent.reasoning else ""

    # Hour inquiry
    if any(word in message_lower for word in ["hour", "open", "time", "when"]):
        return {
            "text": "We're open every day! 🕐\n\n"
            "**Operating Hours:**\n"
            "Monday – Sunday: 8:00 AM – 7:30 PM\n\n"
            "We're here to serve you 7 days a week!"
        }

    # Location inquiry
    if any(word in message_lower for word in ["location", "where", "address", "find"]):
        return {
            "text": "📍 **Our Location:**\n"
            "1st Floor, Valley Arcade Mall, Nairobi\n\n"
            "**Contact Us:**\n"
            "📞 +254 712 345 678\n"
            "📧 info@glowhavenbeauty.co.ke\n"
            "📱 Instagram: @glowhavenbeautylounge"
        }

    # Promotions inquiry
    if any(
        word in message_lower
        for word in ["promo", "deal", "discount", "offer", "special"]
    ):
        promo_text = "🎉 **Current Promotions:**\n\n"
        for promo in PROMOTIONS:
            promo_text += f"**{promo['name']}**\n"
            promo_text += f"{promo['description']}\n"
            promo_text += f"Valid: {promo['valid_until']}\n\n"
        return {"text": promo_text}

    # Services overview
    if any(word in message_lower for word in ["service", "what do you", "offer"]):
        services_text = "✨ **Our Services:**\n\n"
        for category in SERVICES.keys():
            services_text += f"• {category}\n"
        services_text += (
            "\n💰 Prices range from KES 700 - 3,500\n"
            "Would you like to see specific service prices or book an appointment?"
        )
        return {"text": services_text}

    # Default general response
    greeting = f"Hi {customer_name}!" if customer_name else "Hello!"
    return {
        "text": f"{greeting} Welcome to Glow Haven Beauty Lounge! 🌟\n\n"
        f"I can help you with:\n"
        f"• Booking appointments\n"
        f"• Viewing our services and prices\n"
        f"• Checking our location and hours\n"
        f"• Learning about current promotions\n\n"
        f"What would you like to know?"
    }


def _handle_price_check(intent) -> dict:
    """Handle price check inquiry."""
    entities = intent.entities or {}
    service_category = entities.get("service_category", "").lower()

    # If specific category mentioned, show that category
    if service_category:
        for category, services in SERVICES.items():
            if service_category in category.lower():
                price_text = f"💰 **{category} Prices:**\n\n"
                for service in services:
                    price_text += (
                        f"• {service['name']}: KES {service['price']:,} "
                        f"({service['duration']})\n"
                    )
                price_text += "\nWould you like to book any of these services?"
                return {"text": price_text}

    # Show all prices
    price_text = "💰 **Our Service Prices:**\n\n"
    for category, services in SERVICES.items():
        price_text += f"**{category}:**\n"
        for service in services:
            price_text += (
                f"• {service['name']}: KES {service['price']:,} "
                f"({service['duration']})\n"
            )
        price_text += "\n"
    price_text += "Ready to book? Just let me know! 💅"
    return {"text": price_text}


def _handle_feedback_intent(customer_name: str | None) -> dict:
    """Handle feedback intent - transition to feedback flow."""
    greeting = f"Thank you, {customer_name}!" if customer_name else "Thank you!"
    return {
        "text": f"{greeting} We value your feedback. "
        f"Let me help you share your experience with us.",
        "transition_to": ConversationState.FEEDBACK_RATING,
    }


def _handle_payment_inquiry() -> dict:
    """Handle payment-related inquiry."""
    return {
        "text": "💳 **Payment Information:**\n\n"
        "We accept the following payment methods:\n"
        "• M-Pesa (Pochi la Biashara)\n"
        "• Visa & Mastercard\n"
        "• Cash\n\n"
        "**Booking Policy:**\n"
        "A 30% deposit is required to confirm your appointment. "
        "You can pay the deposit via M-Pesa when booking.\n\n"
        "Would you like to book an appointment?"
    }


def _handle_unknown_intent(customer_name: str | None) -> dict:
    """Handle unknown intent."""
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
    """Handler for IDLE state - uses LLM intent recognition for routing."""

    def __init__(self):
        """Initialize handler with intent recognition service."""
        self.intent_service = IntentRecognitionService()

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.info(
            "Handling IDLE state with intent recognition",
            session_id=session.id,
            phone_number=session.phone_number,
            message_preview=message_content[:50],
        )

        # Recognize intent from a message
        intent = await self.intent_service.recognize_intent(message_content)

        app_logger.info(
            "Intent recognized in IDLE handler",
            session_id=session.id,
            intent_type=intent.type.value,
            confidence=intent.confidence,
        )

        # Check if clarification needed (low confidence)
        if intent.confidence < 0.7:
            return _handle_low_confidence(customer_name)

        # Route based on intent type
        if intent.type == IntentType.BOOK_APPOINTMENT:
            return _handle_booking_intent(customer_name)

        elif intent.type == IntentType.GENERAL_INQUIRY:
            return _handle_general_inquiry(intent, customer_name)

        elif intent.type == IntentType.PRICE_CHECK:
            return _handle_price_check(intent)

        elif intent.type == IntentType.FEEDBACK:
            return _handle_feedback_intent(customer_name)

        elif intent.type == IntentType.PAYMENT_RELATED:
            return _handle_payment_inquiry()

        else:  # UNKNOWN
            return _handle_unknown_intent(customer_name)
