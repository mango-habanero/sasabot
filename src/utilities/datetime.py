"""DateTime utilities for booking flow."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.configuration import settings


def timezone_now() -> datetime:
    return datetime.now(ZoneInfo(settings.TIMEZONE))


def get_next_days(count: int = 7) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    days = []

    for i in range(count):
        target_date = today + timedelta(days=i)
        days.append(
            {
                "date": target_date.isoformat(),  # "2025-11-01"
                "display": target_date.strftime("%A, %B %d"),  # "Friday, November 01"
                "day_name": target_date.strftime("%A"),  # "Friday"
                "is_today": i == 0,
            }
        )

    return days


def get_time_slots() -> list[dict]:
    slots = []

    for hour in range(9, 19):
        time_obj = datetime.strptime(f"{hour:02d}:00", "%H:%M").time()
        slots.append(
            {
                "time": time_obj.strftime("%H:%M"),  # "14:00"
                "display": time_obj.strftime("%I:%M %p").lstrip("0"),  # "2:00 PM"
                "hour": hour,
            }
        )

    return slots


def format_datetime_display(date_str: str, time_str: str) -> str:
    date_obj = datetime.fromisoformat(date_str)
    time_obj = datetime.strptime(time_str, "%H:%M").time()

    date_part = date_obj.strftime("%A, %B %d").replace(
        " 0", " "
    )  # Remove leading zero from day
    time_part = time_obj.strftime("%I:%M %p").lstrip("0")  # "2:00 PM"

    return f"{date_part} at {time_part}"


def is_valid_business_hours(time_str: str) -> bool:
    try:
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        hour = time_obj.hour

        # 8am (8) to 7pm (19)
        return 8 <= hour <= 19
    except ValueError:
        return False


def generate_date_id(date_str: str) -> str:
    return f"date_{date_str}"


def generate_time_id(time_str: str) -> str:
    return f"time_{time_str}"


def parse_date_id(date_id: str) -> str | None:
    if date_id.startswith("date_"):
        return date_id[5:]  # Remove "date_" prefix
    return None


def parse_time_id(time_id: str) -> str | None:
    if time_id.startswith("time_"):
        return time_id[5:]  # Remove "time_" prefix
    return None
