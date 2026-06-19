from __future__ import annotations

import logging


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
