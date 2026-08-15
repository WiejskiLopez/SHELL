from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.context import get_causation_id, get_correlation_id

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )


class SqlCommandOutboxPublisher:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: CommandDeliveryModels,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_model = models.outbox

    async def publish(
        self,
        command_type: str,
        payload: dict[str, object],
        occurred_at: datetime,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                self._outbox_model(
                    id=str(uuid.uuid4()),
                    command_type=command_type,
                    occurred_at=occurred_at,
                    payload=payload,
                    correlation_id=get_correlation_id(),
                    causation_id=get_causation_id(),
                )
            )
            await session.commit()
