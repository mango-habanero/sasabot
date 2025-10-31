##!/usr/bin/env python3
"""SasaBot application entrypoint."""

from . import __version__
from .configuration import settings
from .configuration.logger import configure_logging

configure_logging(
    enable_json=settings.STRUCTURED_LOGGING_ENABLED,
    level=settings.LOG_LEVEL,
)

from .common.system import create_app  # noqa


def main():
    return create_app(
        description="WhatsApp chatbot for beauty salon bookings with AI-powered conversations, M-PESA payment integration, and automated receipt generation",
        title="SasaBot APIs",
        version=__version__,
    )


app = main()
