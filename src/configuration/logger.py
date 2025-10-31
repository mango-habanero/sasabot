import logging
import sys

import structlog
from structlog.typing import Processor


def configure_logging(enable_json: bool = False, level: str = "INFO") -> None:
    """
    Configures the logging system, setting up structured logging with optional
    JSON formatting and specific log level.

    :param enable_json: If True, enables JSON formatting for log messages;
        otherwise, logs are output in a human-readable format.
    :type enable_json: bool
    :param level: The logging level as a string (e.g., "DEBUG", "INFO"). Defaults
        to "INFO".
    :type level: str
    :return: None
    """

    # convert level to numeric value once
    log_level = getattr(logging, level.upper(), logging.INFO)

    # set up the root logger to direct all output to stdout
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # define shared processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.CallsiteParameterAdder(
            [structlog.processors.CallsiteParameter.PATHNAME]
        ),
        structlog.processors.JSONRenderer()
        if enable_json
        else structlog.dev.ConsoleRenderer(colors=True),
    ]

    structlog.configure_once(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # hook uncaught exceptions
    def _handle_uncaught(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        structlog.get_logger("system").error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = _handle_uncaught

    structlog.get_logger("system").debug(
        "Logging configured", json_format=enable_json, level=level.upper()
    )


app_logger = structlog.get_logger("system")
