"""context.py
Context — execution context passed to internal functions.

Slots:
"""

from __future__ import annotations

from shell.context.context.internal._init_context import _init_context


class Context:
    """Execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_context(self) -> None:
        _init_context(self)
