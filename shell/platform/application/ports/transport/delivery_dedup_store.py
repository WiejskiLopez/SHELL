"""DeliveryDedupStore port for explicit at-least-once deduplication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime


class DeliveryDedupStore(Protocol):
    """Records and checks idempotency of processed deliveries."""

    async def is_duplicate(self, outbox_id: str) -> bool:
        """Return ``True`` when this consumer already processed ``outbox_id``."""
        ...

    async def mark_processed(
        self,
        outbox_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        """Record ``outbox_id`` as processed by this consumer."""
        ...
