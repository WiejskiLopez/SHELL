"""SQLite integration tests for the shared OutboxToTransportRelay."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.payloads.ingestion_payload import (
    IngestionPayload,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (
    IngestionData,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.types import JsonStr
from shell.tests.platform.integration.platform_delivery_models import MESSAGE_DELIVERY_MODELS

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope

_OUTBOX_MODEL: Any = MESSAGE_DELIVERY_MODELS.outbox


def _message() -> IngestionPayload:
    return IngestionPayload(
        occurred_at=OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
        ingestion_data=IngestionData(JsonStr(json.dumps({"type": "test"}))),
    )


class RecordingTransport:
    def __init__(self) -> None:
        self.envelopes: list[DeliveryEnvelope] = []

    async def deliver(self, envelope: DeliveryEnvelope) -> None:
        self.envelopes.append(envelope)


async def test_message_outbox_uses_shared_transport_relay(
    session_factory: async_sessionmaker,
) -> None:
    await SqlMessageOutboxPublisher(session_factory, MESSAGE_DELIVERY_MODELS).publish([_message()])
    transport = RecordingTransport()
    relay = OutboxToTransportRelay(
        session_factory,
        MESSAGE_DELIVERY_MODELS,
        transport,
        kind="message",
    )

    assert await relay.run_once() == 1
    assert len(transport.envelopes) == 1
    assert transport.envelopes[0].contract_type == "IngestionPayload"
    assert transport.envelopes[0].outbox_id
    assert transport.envelopes[0].payload

    async with session_factory() as session:
        row = (await session.execute(select(_OUTBOX_MODEL))).scalar_one()
    assert row.published_at is not None
