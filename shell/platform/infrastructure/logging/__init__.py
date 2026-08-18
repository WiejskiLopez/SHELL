"""Stdlib logging adapter."""

from __future__ import annotations

import logging

__all__ = [
    "StdlibLogger",
]


class StdlibLogger:
    """Implements application/ports/logger.Logger using stdlib logging."""

    def __init__(self, name: str = "shell") -> None:
        self._log = logging.getLogger(name)

    def debug(self, msg: str, **kw: object) -> None:
        self._log.debug(msg, extra=kw)

    def info(self, msg: str, **kw: object) -> None:
        self._log.info(msg, extra=kw)

    def warning(self, msg: str, **kw: object) -> None:
        self._log.warning(msg, extra=kw)

    def error(self, msg: str, **kw: object) -> None:
        self._log.error(msg, extra=kw)
