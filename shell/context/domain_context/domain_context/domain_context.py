"""domain_context.py
DomainContext — domain-level execution context.

Slots:
"""

from __future__ import annotations

from shell.context.domain_context.domain_context.internal._init_domain_context import _init_domain_context


class DomainContext:
    """Domain-level execution context.

    Slots:
    """

    __slots__ = ()

    def __init__(self) -> None:
        pass

    def init_domain_context(self) -> None:
        _init_domain_context(self)
