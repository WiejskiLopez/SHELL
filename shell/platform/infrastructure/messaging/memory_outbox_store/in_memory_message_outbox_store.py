from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from shell.platform.infrastructure.context import get_causation_id, get_correlation_id
from shell.platform.infrastructure.messaging.memory_outbox_store.message_outbox_record import (
    MessageOutboxRecord,
)
from shell.platform.infrastructure.serialization import DomainMessageSerializer

if TYPE_CHECKING:
    from shell.platform.domain.messages import DomainMessage


class InMemoryMessageOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlMessageOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[MessageOutboxRecord] = []

    async def publish(self, messages: list[DomainMessage]) -> None:
        correlation_id = get_correlation_id()
        causation_id = get_causation_id()
        serializer = DomainMessageSerializer()
        for message in messages:
            try:
                payload = serializer.to_payload(message)
                self.records.append(
                    MessageOutboxRecord(
                        id=str(uuid.uuid4()),
                        message_type=type(message).__name__,
                        occurred_at=message.occurred_at.value,
                        payload=payload,
                        correlation_id=correlation_id,
                        causation_id=causation_id,
                    )
                )
            except Exception:
                logging.getLogger(__name__).critical(
                    "Failed to serialize message %s — message LOST", type(message).__name__
                )
                raise

    def pending(self) -> list[MessageOutboxRecord]:
        return [record for record in self.records if not record.is_published]
