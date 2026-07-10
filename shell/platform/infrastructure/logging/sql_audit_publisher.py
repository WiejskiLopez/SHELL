"""SqlAuditPublisher — persists domain events to the audit_event table."""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.sql.models import AuditEventModel
from shell.platform.infrastructure.serialization import DomainEventSerializer

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.domain.events import DomainEvent


class SqlAuditPublisher:
    """EventPublisher adapter that writes one row per domain event to ``audit_event``."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        serializer = DomainEventSerializer()
        async with self._session_factory() as session:
            for event in events:
                try:
                    payload = serializer.to_payload(event)
                    session.add(
                        AuditEventModel(
                            id=str(uuid.uuid4()),
                            event_type=type(event).__name__,
                            occurred_at=event.occurred_at.value,
                            payload=payload,
                        )
                    )
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Failed to serialize audit event %s", type(event).__name__
                    )
                    continue
            await session.commit()
