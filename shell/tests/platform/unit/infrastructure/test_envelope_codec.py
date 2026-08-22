"""Unit tests for the platform EnvelopeCodec."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.platform.application.ports.transport.delivery_transport import DeliveryEnvelope
from shell.platform.infrastructure.messaging.transport import EnvelopeCodec


def _envelope() -> DeliveryEnvelope:
    return DeliveryEnvelope(
        kind="event",
        outbox_id="outbox-1",
        contract_type="TaskExecutionCreatedEvent",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"task_execution_id": "abc"},
        correlation_id="corr-1",
        causation_id="cause-1",
        event_id="event-1",
        aggregate_id="aggregate-1",
        aggregate_name="TaskExecution",
        schema_version=2,
    )


class TestEnvelopeCodec:
    def test_round_trip_preserves_fields(self) -> None:
        codec = EnvelopeCodec()
        encoded = codec.encode(_envelope())
        decoded = codec.decode(encoded)

        assert decoded.kind == "event"
        assert decoded.outbox_id == "outbox-1"
        assert decoded.contract_type == "TaskExecutionCreatedEvent"
        assert decoded.occurred_at == datetime(2026, 1, 1, tzinfo=UTC)
        assert decoded.payload == {"task_execution_id": "abc"}
        assert decoded.correlation_id == "corr-1"
        assert decoded.causation_id == "cause-1"
        assert decoded.event_id == "event-1"
        assert decoded.aggregate_id == "aggregate-1"
        assert decoded.aggregate_name == "TaskExecution"
        assert decoded.schema_version == 2

    def test_naive_occurred_at_normalized_to_utc(self) -> None:
        codec = EnvelopeCodec()
        raw = codec.encode(_envelope()).replace(
            b"2026-01-01T00:00:00+00:00", b"2026-01-01T00:00:00"
        )
        decoded = codec.decode(raw)
        assert decoded.occurred_at.tzinfo is not None

    def test_event_type_is_a_wire_envelope_field(self) -> None:
        encoded = EnvelopeCodec().encode(_envelope())

        assert b'"event_type":"TaskExecutionCreatedEvent"' in encoded
        assert b'"contract_type"' not in encoded
        assert b'"outbox_id":"outbox-1"' in encoded
        assert b'"schema_version":2' in encoded

    def test_decode_rejects_unknown_kind(self) -> None:
        codec = EnvelopeCodec()
        raw = codec.encode(_envelope()).replace(b'"kind":"event"', b'"kind":"unknown"')
        try:
            codec.decode(raw)
        except ValueError as exc:
            assert "kind" in str(exc)
        else:
            raise AssertionError("expected ValueError for unknown kind")
