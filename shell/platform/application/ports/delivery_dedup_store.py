"""DeliveryDedupStore — port for explicit at-least-once deduplication.

The inbox processor commits the business change, the local outbox and the inbox
acknowledge in one transaction via the ambient session scope (ref2.md §4.1), so
SQL handlers that share the processor's session need no extra dedup row.

This port exists for handlers that CANNOT share the processor's transaction
(separate database / non-shared unit of work). Such a handler:

1. receives a ``DeliveryDedupStore`` (via DI);
2. writes its business effect and calls ``mark_processed`` in ONE unit of work;
3. on redelivery the processor consults ``is_duplicate`` before dispatch and
   never runs the handler twice.

The store resolves its session from the active delivery session scope, so the
dedup row is always written in the same transaction as the business effect.
A unique-key conflict (``(consumer_name, delivery_id)``) means the delivery was
already processed and is treated as success — never written in a separate
transaction before the business effect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime


class DeliveryDedupStore(Protocol):
    """Records and checks idempotency of processed deliveries."""

    async def is_duplicate(self, delivery_id: str) -> bool:
        """Return ``True`` when this consumer already processed ``delivery_id``.

        Resolves its session from the active delivery session scope. Must be
        called from inside the processor's processing transaction (or a handler
        unit of work sharing it).
        """
        ...

    async def mark_processed(
        self,
        delivery_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        """Record ``delivery_id`` as processed by this consumer.

        Must be called atomically with the business effect (same unit of work /
        same session scope). A unique-key conflict is a no-op — the delivery was
        already processed.
        """
        ...
