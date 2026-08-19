"""DeliveryDedupStore port for explicit at-least-once deduplication."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime


class DeliveryDedupStore(Protocol):
    """Records and checks idempotency of processed deliveries."""

    async def is_duplicate(self, delivery_id: str) -> bool:
        """Return ``True`` when this consumer already processed ``delivery_id``."""
        ...

    async def mark_processed(
        self,
        delivery_id: str,
        *,
        payload: dict[str, object] | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        """Record ``delivery_id`` as processed by this consumer."""
        ...
