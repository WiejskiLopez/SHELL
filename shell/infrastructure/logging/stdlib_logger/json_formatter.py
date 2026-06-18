from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from shell.infrastructure.logging.stdlib_logger._context import get_correlation_id


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        _std_keys = logging.LogRecord.__dict__.keys() | {"message", "asctime", "TaskExecutionName"}
        for key, value in record.__dict__.items():
            if key not in _std_keys and not key.startswith("_"):
                data.setdefault("extra", {})[key] = value  # type: ignore[index]
        return json.dumps(data, default=str)
