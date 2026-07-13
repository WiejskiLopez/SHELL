from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.infrastructure.messaging.messaging.envelope import Envelope
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr


def _sample_message() -> MessageRouter:
    return MessageRouter.new(
        id_=MessageId.generate(),
        message_data=MessageData(JsonStr(json.dumps({"type": "test.event"}))),
        now=CreatedAt.from_datetime(datetime.now(tz=UTC)),
    )


class TestEnvelope:
    def test_from_message_sets_message_id(self) -> None:
        msg = _sample_message()
        envelope = Envelope.from_message(
            message=msg,
            trace_id="trace-1",
            sender_service="svc-a",
            receiver_service="svc-b",
            transport_metadata={},
        )
        assert envelope.message_id == msg.id.value
        assert envelope.trace_id == "trace-1"

    def test_from_message_with_correlation_id(self) -> None:
        msg = _sample_message()
        envelope = Envelope.from_message(
            message=msg,
            trace_id="trace-2",
            sender_service="svc-a",
            receiver_service="svc-b",
            transport_metadata={},
            correlation_id="corr-789",
        )
        assert envelope.transport_metadata.get("correlation_id") == "corr-789"

    def test_from_message_without_correlation_id(self) -> None:
        msg = _sample_message()
        envelope = Envelope.from_message(
            message=msg,
            trace_id="trace-3",
            sender_service="svc-a",
            receiver_service="svc-b",
            transport_metadata={},
        )
        assert "correlation_id" not in envelope.transport_metadata

    def test_to_dict_round_trip(self) -> None:
        msg = _sample_message()
        original = Envelope.from_message(
            message=msg,
            trace_id="trace-4",
            sender_service="svc-a",
            receiver_service="svc-b",
            transport_metadata={},
            correlation_id="corr-roundtrip",
        )
        data = original.to_dict()
        restored = Envelope.from_dict(data)
        assert restored.envelope_id == original.envelope_id
        assert restored.message_id == original.message_id
        assert restored.trace_id == original.trace_id
        assert restored.transport_metadata == original.transport_metadata
