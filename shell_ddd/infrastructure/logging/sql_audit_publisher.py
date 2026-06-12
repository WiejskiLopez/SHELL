"""SqlAuditPublisher — persists domain events to the audit_event table."""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.domain.events.events import DomainEvent


class SqlAuditPublisher:
    """EventPublisher adapter that writes one row per domain event to ``audit_event``."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        async with self._session_factory() as session:
            for event in events:
                payload = {
                    f.name: str(getattr(event, f.name))
                    for f in dataclasses.fields(event)  # type: ignore[arg-type]
                    if f.name != "occurred_at"
                }
                session.add(
                    AuditEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                    )
                )
            await session.commit()
