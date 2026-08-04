import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..configs.config_loader import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if hasattr(record, "service"):
            payload["service"] = record.service
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=10_000_000, backupCount=5)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(JsonFormatter())
    root.addHandler(stream_handler)


configure_logging()
