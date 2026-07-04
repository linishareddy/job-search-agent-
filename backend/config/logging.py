import json
import logging
import sys

from config.settings import settings


class JsonFormatter(logging.Formatter):
    """Minimal structured formatter — one JSON object per line, no new dependency.

    Pipeline logs already carry a de facto correlation ID as a `[Run {run.id}]`
    prefix in the message (see services/pipeline/orchestrator.py); this formatter
    doesn't change that convention, it just makes every line machine-parseable
    (by level, logger, timestamp) around it.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    logging.basicConfig(level=log_level, handlers=[handler])

    # Quiet noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
