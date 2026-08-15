"""SqlMessageOutboxPublisher — MessagePublisher adapter that writes to outbox_message table.

Messages are stored in a dedicated DB session so they survive even if the caller's
transaction was already committed.  A MessageOutboxToInboxRelay then reads them and
forwards them to the MessageBus.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.serialization import DomainMessageSerializer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
        MessageDeliveryModels,
    )


class SqlMessageOutboxPublisher:
    """Writes domain messages to the ``outbox_message`` table (own session per call)."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        models: MessageDeliveryModels,
    ) -> None:
        self._session_factory = session_factory
        self._outbox_model = models.outbox

    async def publish(self, messages: Sequence[object]) -> None:
        if not messages:
            return
        correlation_id = get_correlation_id()
        causation_id = get_causation_id()
        serializer = DomainMessageSerializer()
        async with self._session_factory() as session:
            for message in messages:
                try:
                    payload = serializer.to_payload(message)
                    session.add(
                        self._outbox_model(
                            id=str(uuid.uuid4()),
                            message_type=type(message).__name__,
                            occurred_at=message.occurred_at.value,  # type: ignore[attr-defined]
                            payload=payload,
                            correlation_id=correlation_id,
                            causation_id=causation_id,
                            published_at=None,
                        )
                    )
                except Exception:
                    logging.getLogger(__name__).critical(
                        "Failed to serialize message %s — message LOST", type(message).__name__
                    )
                    raise
            await session.commit()
