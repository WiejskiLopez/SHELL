"""system_context.py
SystemContext — system-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.system_context.system_context.internal._init_system_context import _init_system_context


class SystemContext:
    """System-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_system_context(self) -> None:
        _init_system_context(self)
