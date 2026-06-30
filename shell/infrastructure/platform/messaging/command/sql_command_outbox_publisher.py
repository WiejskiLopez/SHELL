from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.infrastructure.platform.context import get_causation_id, get_correlation_id
from shell.infrastructure.platform.persistence.sql.models.command import OutboxCommandModel

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import async_sessionmaker


class SqlCommandOutboxPublisher:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory

    async def publish(
        self,
        command_type: str,
        payload: dict,
        occurred_at: datetime,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                OutboxCommandModel(
                    id=str(uuid.uuid4()),
                    command_type=command_type,
                    occurred_at=occurred_at,
                    payload=payload,
                    correlation_id=get_correlation_id(),
                    causation_id=get_causation_id(),
                )
            )
            await session.commit()
