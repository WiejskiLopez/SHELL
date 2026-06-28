"""Structured JSON logger — implements the Logger port using stdlib logging."""

from __future__ import annotations

import logging

from shell.infrastructure.platform.context import (
    correlation_id_var,  # noqa: F401 — re-export dla konsumentów
    get_correlation_id,  # noqa: F401 — re-export dla konsumentów
    set_correlation_id,  # noqa: F401 — re-export dla konsumentów
)
from shell.infrastructure.platform.logging.stdlib_logger.json_formatter import JsonFormatter
from shell.infrastructure.platform.logging.stdlib_logger.stdlib_logger import (
    StdlibLogger,  # noqa: F401 — re-export dla konsumentów
)

__all__ = [
    "StdlibLogger",
    "JsonFormatter",
    "correlation_id_var",
    "get_correlation_id",
    "set_correlation_id",
]


def _make_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    return handler
