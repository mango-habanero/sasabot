"""Business context for Glow Haven Beauty Lounge."""

import re

BUSINESS_INFO = """
Business Name: Glow Haven Beauty Lounge
Location: 1st Floor, Valley Arcade Mall, Nairobi
Operating Hours: Monday – Sunday, 8:00 AM – 7:30 PM
Contact: +254 712 345 678
Email: info@glowhavenbeauty.co.ke
Instagram: @glowhavenbeautylounge

Booking Policy:
- 30% deposit required to confirm appointments
- Cancellations must be made 6 hours in advance
- Payment methods: M-Pesa, Cash
"""

SERVICES = {
    "Hair Care": [
        {"name": "Wash & Blow Dry", "price": 1000, "duration": "45 mins"},
        {"name": "Silk Press", "price": 2000, "duration": "1 hr 15 mins"},
        {"name": "Braiding (Medium)", "price": 3500, "duration": "3 hrs"},
        {"name": "Wig Installation", "price": 2500, "duration": "1 hr"},
    ],
    "Nail Care": [
        {"name": "Classic Manicure", "price": 800, "duration": "45 mins"},
        {"name": "Gel Manicure", "price": 1200, "duration": "1 hr"},
        {"name": "Pedicure", "price": 1500, "duration": "1 hr 15 mins"},
    ],
    "Facial Treatments": [
        {"name": "Express Facial", "price": 1200, "duration": "30 mins"},
        {"name": "Deep Cleansing Facial", "price": 2000, "duration": "1 hr"},
        {"name": "Anti-Aging Facial", "price": 3000, "duration": "1 hr 15 mins"},
    ],
    "Massage": [
        {"name": "Swedish Massage", "price": 2800, "duration": "1 hr"},
        {"name": "Deep Tissue Massage", "price": 3200, "duration": "1 hr 15 mins"},
        {"name": "Aromatherapy Massage", "price": 3000, "duration": "1 hr"},
    ],
    "Makeup & Lashes": [
        {"name": "Day Makeup", "price": 1800, "duration": "45 mins"},
        {"name": "Glam Makeup", "price": 2800, "duration": "1 hr 15 mins"},
        {"name": "Lash Extension (Classic)", "price": 3500, "duration": "1 hr 30 mins"},
    ],
    "Waxing": [
        {"name": "Underarm Wax", "price": 700, "duration": "20 mins"},
        {"name": "Full Leg Wax", "price": 1800, "duration": "45 mins"},
        {"name": "Brazilian Wax", "price": 2000, "duration": "45 mins"},
    ],
}

PROMOTIONS = [
    {
        "name": "Midweek Glow Deal",
        "description": "15% off all hair and nail services every Tuesday & Wednesday",
        "valid_until": "31 Oct 2025",
    },
    {
        "name": "Refer & Shine",
        "description": "Get KES 500 off your next visit when you refer a new client",
        "valid_until": "31 Oct 2025",
    },
    {
        "name": "Student Discount",
        "description": "Show your student ID and enjoy 10% off all services",
        "valid_until": "Ongoing",
    },
    {
        "name": "Spa Day Duo",
        "description": "Book any 2 treatments (Facial + Massage) and get 1 free add-on service",
        "valid_until": "31 Oct 2025",
    },
    {
        "name": "Birthday Treat",
        "description": "Celebrate your birthday month with a complimentary manicure",
        "valid_until": "Ongoing",
    },
]


def _slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    :param text: Text to slugify
    :return: Lowercase slug with underscores
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces, ampersands, and special chars with underscores
    slug = re.sub(r"[&\s\-]+", "_", slug)
    # Remove parentheses and their contents
    slug = re.sub(r"\([^)]*\)", "", slug)
    # Remove any remaining non-alphanumeric chars except underscores
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    # Remove duplicate underscores
    slug = re.sub(r"_+", "_", slug)
    # Strip leading/trailing underscores
    slug = slug.strip("_")
    return slug


def generate_service_id(category: str, service_name: str) -> str:
    """
    Generate unique service ID from category and service name.

    :param category: Service category (e.g., "Hair Care")
    :param service_name: Service name (e.g., "Silk Press")
    :return: Service ID (e.g., "hair_care_silk_press")
    """
    category_slug = _slugify(category)
    service_slug = _slugify(service_name)
    return f"{category_slug}_{service_slug}"


def generate_category_id(category: str) -> str:
    """
    Generate category ID from category name.

    :param category: Category name (e.g., "Hair Care")
    :return: Category ID (e.g., "category_hair_care")
    """
    return f"category_{_slugify(category)}"


def get_service_categories() -> list[str]:
    """
    Get list of all service category names.

    :return: List of category names
    """
    return list(SERVICES.keys())


def get_services_by_category(category: str) -> list[dict] | None:
    """
    Get all services for a specific category.

    :param category: Category name (e.g., "Hair Care")
    :return: List of service dicts or None if category not found
    """
    return SERVICES.get(category)


def find_service_by_id(service_id: str) -> dict | None:
    """
    Find a service by its generated ID.

    :param service_id: Service ID (e.g., "hair_care_silk_press")
    :return: Service dict with category added, or None if not found
    """
    for category, services in SERVICES.items():
        for service in services:
            if generate_service_id(category, service["name"]) == service_id:
                # Return service with category included
                return {
                    **service,
                    "category": category,
                }
    return None


def find_category_by_id(category_id: str) -> str | None:
    """
    Find category name by its ID.

    :param category_id: Category ID (e.g., "category_hair_care")
    :return: Category name or None if not found
    """
    if not category_id.startswith("category_"):
        return None

    for category in SERVICES.keys():
        if generate_category_id(category) == category_id:
            return category
    return None


def format_price(price: int) -> str:
    """
    Format price with currency and deposit info.

    :param price: Price in KES
    :return: Formatted price string with deposit
    """
    deposit = int(price * 0.3)
    return f"KES {price} (Deposit: KES {deposit})"


def format_services_for_prompt() -> str:
    """Format services into readable text for LLM prompt."""
    lines = []
    for category, services in SERVICES.items():
        lines.append(f"\n{category}:")
        for service in services:
            lines.append(
                f"  - {service['name']}: KES {service['price']} ({service['duration']})"
            )
    return "\n".join(lines)


def format_promotions_for_prompt() -> str:
    """Format promotions into readable text for LLM prompt."""
    lines = ["\nCurrent Promotions:"]
    for promo in PROMOTIONS:
        lines.append(
            f"  - {promo['name']}: {promo['description']} (Valid: {promo['valid_until']})"
        )
    return "\n".join(lines)
