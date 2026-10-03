import logging
import logging.handlers
import os
from typing import Optional

import structlog


def configure_logging(level: str = "INFO", log_dir: Optional[str] = None) -> None:
    """Configure structured JSON logging for resilience components.

    - Rotating file handler
    - Console output
    - Structlog formatting
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    handlers = []

    console = logging.StreamHandler()
    console.setLevel(log_level)
    handlers.append(console)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        filepath = os.path.join(log_dir, "resilience.log")
        rotating = logging.handlers.RotatingFileHandler(filepath, maxBytes=10 * 1024 * 1024, backupCount=7)
        rotating.setLevel(log_level)
        handlers.append(rotating)

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=handlers,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

