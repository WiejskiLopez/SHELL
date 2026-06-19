"""Structured JSON logger — implements the Logger port using stdlib logging."""

from __future__ import annotations

import logging

from shell.infrastructure.platform.logging.stdlib_logger._context import (
    correlation_id_var,
    get_correlation_id,
    set_correlation_id,
)
from shell.infrastructure.platform.logging.stdlib_logger.json_formatter import JsonFormatter
from shell.infrastructure.platform.logging.stdlib_logger.stdlib_logger import StdlibLogger


def _make_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    return handler
