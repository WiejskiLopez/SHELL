"""Stdlib logging adapter."""
from __future__ import annotations

import logging


class StdlibLogger:
    """Implements application/ports/ports.Logger using Python stdlib logging."""

    def __init__(self, name: str = "shell_ddd") -> None:
        self._log = logging.getLogger(name)

    def debug(self, msg: str, **kw: object) -> None:
        self._log.debug(msg, extra=kw)

    def info(self, msg: str, **kw: object) -> None:
        self._log.info(msg, extra=kw)

    def warning(self, msg: str, **kw: object) -> None:
        self._log.warning(msg, extra=kw)

    def error(self, msg: str, **kw: object) -> None:
        self._log.error(msg, extra=kw)
