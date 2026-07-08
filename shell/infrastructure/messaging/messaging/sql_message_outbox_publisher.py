from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.infrastructure.messaging.persistence.sql.models.outbox_message import (
    OutboxMessageModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.infrastructure.messaging.messaging.envelope import Envelope


class SqlMessageOutboxPublisher:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, envelope: Envelope) -> None:
        now = datetime.now(tz=UTC)
        async with self._session_factory() as session:
            session.add(
                OutboxMessageModel(
                    id=str(uuid.uuid4()),
                    envelope=envelope.to_dict(),
                    created_at=now,
                    published_at=None,
                )
            )
            await session.commit()
