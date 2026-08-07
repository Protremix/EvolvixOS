"""
Standardized logging configuration for EvolvixOS.

Uses structlog for structured JSON logging with support for arbitrary
keyword arguments (request_id, user_id, etc.) in log calls.

Usage:
    from app.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("event_name", request_id="abc123", user_id="xyz")
"""

import logging
import sys
import os
import structlog


def setup_logging(json_mode: bool | None = None, level: str = "INFO") -> None:
    """Configure structlog for structured logging.

    Args:
        json_mode: True for JSON output, False for human-readable. Default: auto (JSON in prod, text in dev).
        level: Log level (DEBUG, INFO, WARNING, ERROR).
    """
    if json_mode is None:
        json_mode = os.getenv("LOG_FORMAT", "json") == "json"

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_mode:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "evolvixos") -> structlog.stdlib.BoundLogger:
    """Return a configured structlog logger instance.

    Supports arbitrary kwargs in log calls:
        logger.info("user_login", user_id="123", ip="10.0.0.1")
    """
    return structlog.get_logger(name)
