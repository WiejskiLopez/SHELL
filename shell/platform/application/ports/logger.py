"""Application port for the cross-cutting logging contract."""

from __future__ import annotations

from typing import Protocol


class Logger(Protocol):
    """Minimal logging contract used by application and infrastructure code."""

    def debug(self, msg: str, **kw: object) -> None: ...
    def info(self, msg: str, **kw: object) -> None: ...
    def warning(self, msg: str, **kw: object) -> None: ...
    def error(self, msg: str, **kw: object) -> None: ...
