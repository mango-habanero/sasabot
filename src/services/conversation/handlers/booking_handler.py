"""Handler for BOOKING_SELECT_SERVICE state."""

from decimal import Decimal

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.services.business import ContextService
from src.services.conversation.handlers.base import BaseStateHandler


def _show_categories(
    business_id: int,
    context_service: ContextService,
    error_message: str | None = None,
) -> dict:
    app_logger.debug("Building category selection list", business_id=business_id)

    categories = context_service.get_categories(business_id)

    rows = []
    for category in categories:
        rows.append(
            {
                "id": str(category.id),
                "title": category.name,
                "description": f"Explore {category.name.lower()} services",
            }
        )

    body_text = "Great! Let's find the perfect service for you. 💅\n\n"
    if error_message:
        body_text = f"⚠️ {error_message}\n\n{body_text}"
    body_text += "Which type of service are you interested in?"

    app_logger.info(
        "Category list prepared",
        business_id=business_id,
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
    category_id: int,
    business_id: int,
    context_service: ContextService,
    error_message: str | None = None,
) -> dict:
    app_logger.debug(
        "Building service list",
        business_id=business_id,
        category_id=category_id,
    )

    category = context_service.get_categories(business_id)
    category_obj = next((c for c in category if c.id == category_id), None)

    if not category_obj:
        app_logger.error(
            "Category not found",
            business_id=business_id,
            category_id=category_id,
        )
        return _show_categories(
            business_id,
            context_service,
            error_message="Something went wrong. Let's start over.",
        )

    services = context_service.get_services_by_category(business_id, category_id)

    if not services:
        app_logger.error(
            "Category has no services",
            business_id=business_id,
            category_id=category_id,
        )
        return _show_categories(
            business_id,
            context_service,
            error_message="Something went wrong. Let's start over.",
        )

    config = context_service.get_configuration(business_id)

    rows = []
    for service in services:
        deposit = (
            Decimal(str(service.price))
            * Decimal(str(config.deposit_percentage))
            / Decimal("100")
        )
        price_text = f"KES {service.price:,.2f} (Deposit: KES {deposit:,.2f})"

        rows.append(
            {
                "id": str(service.id),
                "title": service.name,
                "description": f"{price_text} • {service.duration_minutes} mins",
            }
        )

    body_text = f"Here are our **{category_obj.name}** services:\n\n"
    if error_message:
        body_text = f"⚠️ {error_message}\n\n{body_text}"
    body_text += "Select the service you'd like to book:"

    app_logger.info(
        "Service list prepared",
        business_id=business_id,
        category_id=category_id,
        category_name=category_obj.name,
        service_count=len(services),
        has_error=bool(error_message),
    )

    return {
        "list": {
            "body": body_text,
            "button_text": "Select Service",
            "sections": [{"title": category_obj.name, "rows": rows}],
            "footer": f"All prices include {config.deposit_percentage:.0f}% deposit",
        },
        "update_context": {
            "selected_category": category_obj.name,
            "selected_category_id": category_id,
        },
    }


def _confirm_service_selection(
    service_id: int,
    business_id: int,
    context_service: ContextService,
    customer_name: str | None = None,
) -> dict:
    service = context_service.get_service_by_id(business_id, service_id)
    config = context_service.get_configuration(business_id)

    deposit = (
        Decimal(str(service.price))
        * Decimal(str(config.deposit_percentage))
        / Decimal("100")
    )
    price_text = f"KES {service.price:,.2f}"
    deposit_text = f"KES {deposit:,.2f}"

    greeting = (
        f"Perfect choice, {customer_name}!" if customer_name else "Perfect choice!"
    )

    confirmation_text = (
        f"{greeting}\n\n"
        f"✨ **{service.name}**\n"
        f"💰 {price_text} (Deposit: {deposit_text})\n"
        f"⏱️ {service.duration_minutes} mins\n\n"
        f"Let's schedule your appointment. When would you like to come in?"
    )

    app_logger.info(
        "Service selection confirmed",
        business_id=business_id,
        service_id=service_id,
        service_name=service.name,
        category_id=service.category_id,
        price=float(service.price),
        has_customer_name=bool(customer_name),
    )

    return {
        "text": confirmation_text,
        "update_context": {
            "selected_service_id": service_id,
            "selected_service": {
                "id": service.id,
                "name": service.name,
                "price": float(service.price),
                "duration_minutes": service.duration_minutes,
                "category_id": service.category_id,
            },
        },
        "transition_to": ConversationState.BOOKING_SELECT_DATETIME,
    }


class BookingSelectServiceHandler(BaseStateHandler):
    def __init__(self, context_service: ContextService):
        self.context_service = context_service

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        business_id = session.business_id

        app_logger.info(
            "Handling BOOKING_SELECT_SERVICE state",
            session_id=session.id,
            business_id=business_id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        try:
            selected_id = int(message_content)
        except ValueError:
            app_logger.info(
                "Invalid selection, showing categories",
                session_id=session.id,
                message_content=message_content,
            )
            return _show_categories(business_id, self.context_service)

        categories = self.context_service.get_categories(business_id)
        category_ids = [c.id for c in categories]

        if selected_id in category_ids:
            app_logger.info(
                "Category selected",
                session_id=session.id,
                category_id=selected_id,
            )
            return _show_services(selected_id, business_id, self.context_service)

        try:
            service = self.context_service.get_service_by_id(business_id, selected_id)
            app_logger.info(
                "Service selected",
                session_id=session.id,
                service_id=selected_id,
                service_name=service.name,
            )
            return _confirm_service_selection(
                selected_id, business_id, self.context_service, customer_name
            )
        except Exception:
            app_logger.warning(
                "Service not found, showing categories",
                session_id=session.id,
                attempted_service_id=selected_id,
            )
            return _show_categories(business_id, self.context_service)
