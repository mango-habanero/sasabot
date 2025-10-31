"""Handler for BOOKING_SELECT_SERVICE state."""

from structlog import get_logger

from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.services.conversation.handlers.base import BaseStateHandler
from src.services.llm.business_context import (
    find_category_by_id,
    find_service_by_id,
    format_price,
    generate_category_id,
    generate_service_id,
    get_service_categories,
    get_services_by_category,
)

logger = get_logger(__name__)


def _show_categories(error_message: str | None = None) -> dict:
    """
    Show category selection list.

    :param error_message: Optional error message to prepend
    :return: Response dict with list message
    """
    logger.debug("Building category selection list")

    categories = get_service_categories()

    # Build list rows for categories
    rows = []
    for category in categories:
        category_id = generate_category_id(category)
        rows.append(
            {
                "id": category_id,
                "title": category,
                "description": f"Explore {category.lower()} services",
            }
        )

    body_text = "Great! Let's find the perfect service for you. 💅\n\n"
    if error_message:
        body_text = f"⚠️ {error_message}\n\n{body_text}"
    body_text += "Which type of service are you interested in?"

    logger.info(
        "Category list prepared",
        category_count=len(categories),
        has_error=bool(error_message),
    )

    return {
        "list": {
            "body": body_text,
            "button_text": "View Services",
            "sections": [{"title": "Service Categories", "rows": rows}],
            "footer": "Tap to browse our services",
        }
    }


def _show_services(
    category: str,
    error_message: str | None = None,
) -> dict:
    """
    Show services for selected category.

    :param category: Category name
    :param error_message: Optional error message to prepend
    :return: Response dict with list message and context update
    """
    logger.debug("Building service list", category=category)

    services = get_services_by_category(category)

    if not services:
        logger.error("Category has no services", category=category)
        return _show_categories(error_message="Something went wrong. Let's start over.")

    # Build list rows for services
    rows = []
    for service in services:
        service_id = generate_service_id(category, service["name"])
        price_str = format_price(service["price"])
        rows.append(
            {
                "id": service_id,
                "title": service["name"],
                "description": f"{price_str} • {service['duration']}",
            }
        )

    body_text = f"Here are our **{category}** services:\n\n"
    if error_message:
        body_text = f"⚠️ {error_message}\n\n{body_text}"
    body_text += "Select the service you'd like to book:"

    logger.info(
        "Service list prepared",
        category=category,
        service_count=len(services),
        has_error=bool(error_message),
    )

    return {
        "list": {
            "body": body_text,
            "button_text": "Select Service",
            "sections": [{"title": category, "rows": rows}],
            "footer": "All prices include 30% deposit",
        },
        "update_context": {
            "selected_category": category,
        },
    }


def _confirm_service_selection(
    service: dict,
    customer_name: str | None = None,
) -> dict:
    """
    Confirm service selection and transition to datetime selection.

    :param service: Selected service dict (includes category)
    :param customer_name: Customer name (optional)
    :return: Response dict with confirmation text and transition
    """
    service_id = generate_service_id(service["category"], service["name"])
    price_str = format_price(service["price"])

    greeting = (
        f"Perfect choice, {customer_name}!" if customer_name else "Perfect choice!"
    )

    confirmation_text = (
        f"{greeting}\n\n"
        f"✨ **{service['name']}**\n"
        f"💰 {price_str}\n"
        f"⏱️ {service['duration']}\n\n"
        f"Let's schedule your appointment. When would you like to come in?"
    )

    logger.info(
        "Service selection confirmed",
        service_id=service_id,
        service_name=service["name"],
        category=service["category"],
        price=service["price"],
        has_customer_name=bool(customer_name),
    )

    return {
        "text": confirmation_text,
        "update_context": {
            "selected_service_id": service_id,
            "selected_service": {
                "name": service["name"],
                "price": service["price"],
                "duration": service["duration"],
                "category": service["category"],
            },
        },
        "transition_to": ConversationState.BOOKING_SELECT_DATETIME,
    }


class BookingSelectServiceHandler(BaseStateHandler):
    """Handler for service selection in booking flow."""

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        """
        Handle service selection with message-content-based routing:
        1. If message is category ID -> show services in that category
        2. If message is service ID -> confirm selection and transition
        3. Otherwise -> show categories (first entry or invalid input)

        :param session: Current conversation session
        :param message_content: User's message content (category or service ID)
        :param customer_name: Customer name (optional)
        :return: Response dict with list message or transition
        """
        logger.info(
            "Handling BOOKING_SELECT_SERVICE state",
            session_id=session.id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        # Route based on message content (not context state)

        # Scenario A: User selected a category (message is "category_xxx")
        category_name = find_category_by_id(message_content)
        if category_name:
            logger.info(
                "Category selected",
                session_id=session.id,
                category=category_name,
                category_id=message_content,
            )
            return _show_services(category_name)

        # Scenario B: User selected a service (message is "category_xxx_service_name")
        service = find_service_by_id(message_content)
        if service:
            logger.info(
                "Service selected",
                session_id=session.id,
                service_name=service["name"],
                service_category=service["category"],
                service_id=message_content,
                price=service["price"],
            )
            return _confirm_service_selection(service, customer_name)

        # Scenario C: First entry or unrecognized input - show categories
        logger.info(
            "Showing categories (first entry or unrecognized input)",
            session_id=session.id,
            message_content=message_content,
        )
        return _show_categories()
