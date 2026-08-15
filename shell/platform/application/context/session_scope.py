"""DeliverySessionScope — ambient scope binding one delivery processing UoW.

The inbox processor owns the processing transaction. Before dispatching a
record it opens one session and publishes it as the ambient ``session_scope``
(ContextVar). Any handler-side unit of work entered while the scope is active
reuses that session and defers its commit, so the business change, the local
outbox rows and the inbox acknowledge commit in a single transaction.

Scope semantics (ref2.md §4.1):

- scope = exactly one inbox record and one processing UoW;
- one SQLAlchemy session is never shared across parallel tasks — each record
  gets its own scope/session;
- ``rolled_back`` is set when a handler rolled back its deferred unit of work;
  the processor must then abort the transaction and schedule a retry instead of
  acknowledging.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DeliverySessionScope:
    """A single processing transaction owned by the inbox processor."""

    session: Any
    rolled_back: bool = field(default=False)


session_scope_var: ContextVar[DeliverySessionScope | None] = ContextVar(
    "delivery_session_scope",
    default=None,
)


def get_session_scope() -> DeliverySessionScope | None:
    return session_scope_var.get()


def set_session_scope(scope: DeliverySessionScope) -> Token[DeliverySessionScope | None]:
    return session_scope_var.set(scope)


def reset_session_scope(token: Token[DeliverySessionScope | None]) -> None:
    session_scope_var.reset(token)
