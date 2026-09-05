"""Unit tests for the platform event EnvelopeCodec."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.platform.application.ports.transport.event_transport import EventDeliveryEnvelope
from shell.platform.infrastructure.messaging.event_transport import EnvelopeCodec


def _envelope() -> EventDeliveryEnvelope:
    return EventDeliveryEnvelope(
        event_id="event-1",
        contract_type="TaskExecutionCreatedEvent",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"task_execution_id": "abc"},
        correlation_id="corr-1",
        causation_id="cause-1",
        source_service="execution",
        destination_service="*",
        aggregate_id="aggregate-1",
        schema_version=2,
    )


class TestEnvelopeCodec:
    def test_round_trip_preserves_fields(self) -> None:
        codec = EnvelopeCodec()
        encoded = codec.encode(_envelope())
        decoded = codec.decode(encoded)

        assert decoded.event_id == "event-1"
        assert decoded.contract_type == "TaskExecutionCreatedEvent"
        assert decoded.occurred_at == datetime(2026, 1, 1, tzinfo=UTC)
        assert decoded.payload == {"task_execution_id": "abc"}
        assert decoded.correlation_id == "corr-1"
        assert decoded.causation_id == "cause-1"
        assert decoded.source_service == "execution"
        assert decoded.destination_service == "*"
        assert decoded.aggregate_id == "aggregate-1"
        assert decoded.schema_version == 2

    def test_naive_occurred_at_normalized_to_utc(self) -> None:
        codec = EnvelopeCodec()
        raw = codec.encode(_envelope()).replace(
            b"2026-01-01T00:00:00+00:00", b"2026-01-01T00:00:00"
        )
        decoded = codec.decode(raw)
        assert decoded.occurred_at.tzinfo is not None

    def test_contract_type_is_a_wire_envelope_field(self) -> None:
        encoded = EnvelopeCodec().encode(_envelope())

        assert b'"contract_type":"TaskExecutionCreatedEvent"' in encoded
        assert b'"command_id"' not in encoded
        assert b'"outbox_id"' not in encoded
        assert b'"kind"' not in encoded
        assert b'"schema_version":2' in encoded

    def test_decode_has_no_channel_kind_field(self) -> None:
        codec = EnvelopeCodec()
        encoded = codec.encode(_envelope())
        assert b'"kind"' not in encoded
        assert codec.decode(encoded).contract_type == "TaskExecutionCreatedEvent"