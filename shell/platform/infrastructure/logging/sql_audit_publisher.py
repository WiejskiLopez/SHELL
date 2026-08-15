"""SqlAuditPublisher — persists domain events to the audit_event table."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
        PersistenceDeliveryModels,
    )


class SqlAuditPublisher:
    """EventPublisher adapter that writes one row per domain event to ``audit_event``."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: PersistenceDeliveryModels,
    ) -> None:
        self._session_factory = session_factory
        self._audit_model = models.audit

    async def publish(self, events: Sequence[object]) -> None:
        if not events:
            return
        serializer = DomainEventSerializer()
        async with self._session_factory() as session:
            for event in events:
                try:
                    payload = serializer.to_payload(event)
                    session.add(
                        self._audit_model(
                            id=str(uuid.uuid4()),
                            event_type=type(event).__name__,
                            occurred_at=event.occurred_at.value,  # type: ignore[attr-defined]
                            payload=payload,
                        )
                    )
                except Exception:
                    logging.getLogger(__name__).critical(
                        "Failed to serialize audit event %s — event LOST", type(event).__name__
                    )
                    raise
            await session.commit()
