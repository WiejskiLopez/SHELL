"""session_context.py
SessionContext — session-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.session_context.session_context.internal._init_session_context import _init_session_context


class SessionContext:
    """Session-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_session_context(self) -> None:
        _init_session_context(self)
