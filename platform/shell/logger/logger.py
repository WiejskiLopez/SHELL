"""logger.py
Logger: single-entry-point facade over the underlying logging.Logger.

Consolidates all structured log operations for a node run:
    info()    — informational message
    error()   — error message (does not change status or raise)
    warning() — warning message (does not change status or raise)
"""

from __future__ import annotations

import logging

from shell.logger.internal._get_logger import _get_logger


class Logger:
    """Structured logger for a single node run.

    Wraps the underlying logging.Logger (built and cached by _get_logger)
    and provides domain-aware methods that can mutate app status.

    The underlying logger is lazily resolved on first use through _get_logger,
    which caches the result on app — so Logger(app) is cheap to construct.
    """

    __slots__ = ("_app", "_log_level", "_cached_logger")

    def __init__(self, app) -> None:
        self._app = app
        self._log_level: str | None = None
        self._cached_logger: logging.Logger | None = None

    # -----------------------------------------------------------------------
    # Validated property
    # -----------------------------------------------------------------------

    @property
    def log_level_(self) -> str:
        """Return log_level. Raises if not set."""
        if not self._log_level:
            raise ValueError("[Logger] log_level is not set")
        return self._log_level

    @property
    def cached_logger_(self) -> logging.Logger | None:
        return self._cached_logger

    @cached_logger_.setter
    def cached_logger_(self, value: logging.Logger) -> None:
        self._cached_logger = value

    # ------------------------------------------------------------------ #
    # Logging methods                                                      #
    # ------------------------------------------------------------------ #

    def info(self, message: str) -> None:
        """Log an info message."""
        _get_logger(self._app).info(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """Log an error message. Does not change status or raise."""
        _get_logger(self._app).error(message, exc_info=exc_info)

    def warning(self, message: str) -> None:
        """Log a warning message. Does not change status or raise."""
        _get_logger(self._app).warning(message)
