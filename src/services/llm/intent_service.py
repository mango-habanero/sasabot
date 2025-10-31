"""Intent recognition service using LLM."""

import json

from src.configuration import app_logger
from src.data.dtos.internal.intent import Intent
from src.data.enums.intent import IntentType
from src.services.llm.business_context import (
    BUSINESS_INFO,
    format_promotions_for_prompt,
    format_services_for_prompt,
)
from src.services.llm.client import LLMService


def _build_system_prompt() -> str:
    """
    Build system prompt with business context.

    :return: Complete system prompt for intent recognition
    """
    return f"""You are an AI assistant for Glow Haven Beauty Lounge, a beauty salon in Nairobi.

{BUSINESS_INFO}

Services Offered:{format_services_for_prompt()}

{format_promotions_for_prompt()}

Your task is to analyze customer messages and determine their intent. Classify messages into one of these intents:

1. GENERAL_INQUIRY - This includes:
   - Social greetings: "Hi", "Hello", "Hey", "Good morning", "👋", "Hola", etc.
   - Conversation starters: "How are you?", "What's up?", "How's it going?"
   - Questions about business info: hours, location, services overview, promotions
   - Any friendly opening message that initiates conversation

2. BOOK_APPOINTMENT - Customer wants to book a service or appointment
   - Examples: "I'd like to book", "Can I make an appointment?", "I want to schedule"

3. PRICE_CHECK - Asking about specific service prices or costs
   - Examples: "How much for a manicure?", "What's the price of", "Cost of facial?"

4. PAYMENT_RELATED - Questions or issues about payments, deposits, or M-Pesa
   - Examples: "How do I pay?", "Payment methods?", "Is deposit required?"

5. FEEDBACK - Customer wants to provide feedback, review, or complaint
   - Examples: "I want to give feedback", "I had a bad experience", "Great service!"

6. UNKNOWN - Use ONLY for genuinely ambiguous messages:
   - Context-dependent responses without context: "Yes", "Ok", "Maybe", "Sure"
   - Gibberish or incomprehensible input: "asdfgh", "???", random symbols
   - Messages where even a human would need clarification
   - DO NOT use UNKNOWN for friendly greetings - those are GENERAL_INQUIRY

Extract relevant entities when possible:
- service_category: hair, nails, facial, massage, makeup, waxing
- service_name: specific service mentioned
- time_reference: date/time mentions (e.g., "tomorrow", "2pm", "next week")
- greeting_only: true if message is ONLY a greeting with no other content

Respond ONLY with valid JSON in this exact format:
{{
    "intent_type": "GENERAL_INQUIRY",
    "confidence": 0.95,
    "entities": {{"greeting_only": true}},
    "reasoning": "Simple greeting to initiate conversation"
}}

Confidence scoring guidelines:

For GREETINGS specifically:
- Pure greetings ("Hi", "Hello", "👋"): confidence 0.9-0.95
- Greeting + question ("Hi, what are your hours?"): route to specific intent (0.9+)
- Greeting + clear action ("Hi, I'd like to book"): route to action intent (0.95+)

For other intents:
- 0.9-1.0: Very clear intent with explicit keywords or action verbs
- 0.7-0.89: Clear intent but less explicit phrasing
- 0.5-0.69: Uncertain, needs clarification (rare - most messages have clear intent)
- Below 0.5: Use UNKNOWN intent (very rare)

Important rules:
- Greetings are NEVER UNKNOWN - they are conversation starters (GENERAL_INQUIRY)
- If a message has both greeting + specific intent, classify by the specific intent
- Be generous with confidence scores for clear greetings (0.9+)
- Reserve UNKNOWN only for truly ambiguous or incomprehensible messages"""


class IntentRecognitionService:
    """Service for recognizing user intents from messages."""

    def __init__(self):
        """Initialize intent recognition service."""
        self.llm_service = LLMService()
        self.system_prompt = _build_system_prompt()

    async def recognize_intent(
        self,
        message: str,
        conversation_history: list[str] | None = None,
    ) -> Intent:
        app_logger.info("Recognizing intent", message_preview=message[:50])
        response_text = None
        # Build message context
        user_message = f"Customer message: {message}"
        if conversation_history:
            history_text = "\n".join(conversation_history[-3:])  # Last 3 messages
            user_message = f"Recent conversation:\n{history_text}\n\n{user_message}"

        messages = [{"role": "user", "content": user_message}]

        try:
            # Get LLM response in JSON mode
            response_text = await self.llm_service.complete(
                messages=messages,
                system_prompt=self.system_prompt,
                temperature=0.3,  # Lower temperature for more consistent classification
                max_tokens=500,
            )

            # Parse JSON response
            response_data = json.loads(response_text)

            # Map string intent to enum
            intent_type_str = response_data.get("intent_type", "UNKNOWN")
            try:
                intent_type = IntentType[intent_type_str]
            except KeyError:
                app_logger.warning(
                    "Invalid intent type from LLM",
                    intent_type=intent_type_str,
                )
                intent_type = IntentType.UNKNOWN

            intent = Intent(
                type=intent_type,
                confidence=float(response_data.get("confidence", 0.0)),
                entities=response_data.get("entities", {}),
                reasoning=response_data.get("reasoning"),
            )

            app_logger.info(
                "Intent recognized",
                intent_type=intent.type.value,
                confidence=intent.confidence,
                entities=list(intent.entities.keys()),
            )

            return intent

        except json.JSONDecodeError as e:
            app_logger.error(
                "Failed to parse LLM JSON response",
                error=str(e),
                response_preview=response_text[:100] if response_text else None,
            )
            # Return UNKNOWN intent on parsing error
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                reasoning="Failed to parse LLM response",
            )

        except Exception as e:
            app_logger.error(
                "Intent recognition failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Return UNKNOWN intent on any error
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                entities={},
                reasoning=f"Error: {str(e)}",
            )
