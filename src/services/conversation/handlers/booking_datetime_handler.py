"""Handler for BOOKING_SELECT_DATETIME state."""

from src.configuration import app_logger
from src.data.entities.conversation_session import ConversationSession
from src.data.enums.conversation import ConversationState
from src.services.conversation.handlers.base import BaseStateHandler
from src.utilities import (
    format_datetime_display,
    generate_date_id,
    generate_time_id,
    get_next_days,
    get_time_slots,
    parse_date_id,
    parse_time_id,
)


def _show_dates(error_message: str | None = None) -> dict:
    """
    Show available dates for booking.

    :param error_message: Optional error message to prepend
    :return: Response dict with list message
    """
    app_logger.debug("Building date selection list")

    days = get_next_days(count=7)

    # Build list rows for dates
    rows = []
    for day in days:
        date_id = generate_date_id(day["date"])
        title = "Today" if day["is_today"] else day["display"]
        rows.append(
            {
                "id": date_id,
                "title": title,
                "description": f"{day['day_name']} - Available",
            }
        )

    body_text = "📅 When would you like to come in?\n\n"
    if error_message:
        body_text = f"⚠️ {error_message}\n\n{body_text}"
    body_text += "Select a date for your appointment:"

    app_logger.info(
        "Date list prepared",
        date_count=len(days),
        has_error=bool(error_message),
    )

    return {
        "list": {
            "body": body_text,
            "button_text": "Select Date",
            "sections": [{"title": "Available Dates", "rows": rows}],
            "footer": "Choose any day in the next week",
        }
    }


def _show_time_slots(date_str: str) -> dict:
    """
    Show available time slots for selected date.

    :param date_str: Selected date in ISO format (e.g., "2025-11-01")
    :return: Response dict with list message and context update
    """
    app_logger.debug("Building time slot list", date=date_str)

    slots = get_time_slots()

    # Build list rows for time slots
    rows = []
    for slot in slots:
        time_id = generate_time_id(slot["time"])
        rows.append(
            {
                "id": time_id,
                "title": slot["display"],
                "description": "Available",
            }
        )

    # Get day info for display
    days = get_next_days(count=7)
    selected_day = next((d for d in days if d["date"] == date_str), None)
    day_display = selected_day["display"] if selected_day else date_str

    body_text = f"🕐 What time works best for you on **{day_display}**?\n\n"
    body_text += "Select a time slot:"

    app_logger.info(
        "Time slot list prepared",
        date=date_str,
        slot_count=len(slots),
    )

    return {
        "list": {
            "body": body_text,
            "button_text": "Select Time",
            "sections": [{"title": "Available Times", "rows": rows}],
            "footer": "All times are in your local timezone",
        },
        "update_context": {
            "selected_date": date_str,
        },
    }


def _confirm_datetime(
    date_str: str,
    time_str: str,
    customer_name: str | None = None,
) -> dict:
    # Format datetime for display
    datetime_display = format_datetime_display(date_str, time_str)

    greeting = f"Excellent, {customer_name}!" if customer_name else "Excellent!"

    confirmation_text = (
        f"{greeting}\n\n"
        f"📅 **{datetime_display}**\n\n"
        f"Let me show you a summary of your booking for confirmation."
    )

    app_logger.info(
        "Date and time confirmed",
        date=date_str,
        time=time_str,
        datetime_display=datetime_display,
        has_customer_name=bool(customer_name),
    )

    return {
        "text": confirmation_text,
        "update_context": {
            "selected_time": time_str,
            "selected_datetime_display": datetime_display,
        },
        "transition_to": ConversationState.BOOKING_CONFIRM,
    }


class BookingDateTimeHandler(BaseStateHandler):
    """Handler for date and time selection in booking flow."""

    async def handle(
        self,
        session: ConversationSession,
        message_content: str,
        customer_name: str | None = None,
    ) -> dict:
        app_logger.info(
            "Handling BOOKING_SELECT_DATETIME state",
            session_id=session.id,
            state=session.state.value,
            message_preview=message_content[:50],
            current_context=session.context,
        )

        context = session.context or {}

        # Route based on message content

        # Scenario A: User selected a date (message is "date_YYYY-MM-DD")
        date_str = parse_date_id(message_content)
        if date_str:
            app_logger.info(
                "Date selected",
                session_id=session.id,
                date=date_str,
                date_id=message_content,
            )
            return _show_time_slots(date_str)

        # Scenario B: User selected a time (message is "time_HH:MM")
        time_str = parse_time_id(message_content)
        if time_str:
            # Need the date from context to create full datetime
            selected_date = context.get("selected_date")
            if not selected_date:
                app_logger.error(
                    "Time selected but no date in context",
                    session_id=session.id,
                    time=time_str,
                )
                # Fallback: show dates again
                return _show_dates(
                    error_message="Something went wrong. Let's start over with the date."
                )

            app_logger.info(
                "Time selected",
                session_id=session.id,
                date=selected_date,
                time=time_str,
                time_id=message_content,
            )
            return _confirm_datetime(selected_date, time_str, customer_name)

        # Scenario C: First entry or unrecognized input - show dates
        app_logger.info(
            "Showing dates (first entry or unrecognized input)",
            session_id=session.id,
            message_content=message_content,
        )
        return _show_dates()
