"""Prompt formatter for LLM context generation."""

from src.data.entities.business import (
    Business,
    Location,
    Promotion,
    Service,
    ServiceCategory,
)


def format_business_info(business: Business, location: Location) -> str:
    info_parts = [
        f"Business Name: {business.name}",
        f"Location: {location.address}",
        f"Operating Hours: {format_operating_hours(location.operating_hours)}",
    ]

    if business.phone:
        info_parts.append(f"Contact: {business.phone}")

    if business.email:
        info_parts.append(f"Email: {business.email}")

    if business.instagram_handle:
        info_parts.append(f"Instagram: @{business.instagram_handle}")

    if business.booking_policy_text:
        info_parts.append(f"\nBooking Policy:\n{business.booking_policy_text}")

    return "\n".join(info_parts)


def format_complete_context(
    business: Business,
    location: Location,
    categories: list[ServiceCategory],
    services: list[Service],
    promotions: list[Promotion],
) -> str:
    sections = [
        format_business_info(business, location),
        format_services(categories, services),
    ]

    if promotions:
        sections.append(format_promotions(promotions))

    return "\n\n".join(sections)


def format_operating_hours(operating_hours: dict) -> str:
    days_order = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    hours_parts = []
    for day in days_order:
        if day not in operating_hours:
            continue

        day_info = operating_hours[day]
        day_capitalized = day.capitalize()

        if day_info.get("is_closed", False):
            hours_parts.append(f"{day_capitalized}: Closed")
        else:
            open_time = day_info.get("open", "N/A")
            close_time = day_info.get("close", "N/A")
            hours_parts.append(f"{day_capitalized}: {open_time} - {close_time}")

    return ", ".join(hours_parts) if hours_parts else "Hours not available"


def format_promotions(promotions: list[Promotion]) -> str:
    if not promotions:
        return ""

    lines = ["Current Promotions:"]
    for promo in promotions:
        valid_text = "Ongoing"
        if promo.end_date:
            valid_text = f"Valid until {promo.end_date.strftime('%d %b %Y')}"

        lines.append(f"  - {promo.name}: {promo.description} ({valid_text})")

    return "\n".join(lines)


def format_services(categories: list[ServiceCategory], services: list[Service]) -> str:
    services_by_category = {}
    for service in services:
        if service.category_id not in services_by_category:
            services_by_category[service.category_id] = []
        services_by_category[service.category_id].append(service)

    lines = []
    for category in categories:
        category_services = services_by_category.get(category.id, [])
        if not category_services:
            continue

        lines.append(f"\n{category.name}:")
        for service in category_services:
            lines.append(
                f"  - {service.name}: KES {service.price:,.2f} ({service.duration_minutes} mins)"
            )

    return "\n".join(lines) if lines else "No services available"
