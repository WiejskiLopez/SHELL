"""Structured JSON logger — implements the Logger port using stdlib logging."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Correlation-ID context variable (set per-request/command by middleware or CLI)
# ---------------------------------------------------------------------------

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> None:
    correlation_id_var.set(value)


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


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
        # Include any extra fields attached by the caller
        _std_keys = logging.LogRecord.__dict__.keys() | {"message", "asctime", "taskName"}
        for k, v in record.__dict__.items():
            if k not in _std_keys and not k.startswith("_"):
                data.setdefault("extra", {})[k] = v  # type: ignore[index]
        return json.dumps(data, default=str)


# ---------------------------------------------------------------------------
# Logger adapter
# ---------------------------------------------------------------------------


def _make_handler() -> logging.StreamHandler:  # type: ignore[type-arg]
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    return handler


class StdlibLogger:
    """Implements the ``Logger`` port using stdlib logging with JSON output."""

    def __init__(self, name: str = "shell", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

    def debug(self, msg: str, **kw: object) -> None:
        self._logger.debug(msg, extra=kw if kw else None)

    def info(self, msg: str, **kw: object) -> None:
        self._logger.info(msg, extra=kw if kw else None)

    def warning(self, msg: str, **kw: object) -> None:
        self._logger.warning(msg, extra=kw if kw else None)

    def error(self, msg: str, **kw: object) -> None:
        self._logger.error(msg, extra=kw if kw else None)
