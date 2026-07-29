import logging
import sys
from logging.handlers import RotatingFileHandler
import structlog
from ..configs.config import settings


def configure_logging():
    """Configure structured JSON logging with structlog and RotatingFileHandler."""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    processor_chain = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processor_chain,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # File handler
    fh = RotatingFileHandler("logs/app.log", maxBytes=10_000_000, backupCount=5)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(fh)


configure_logging()
