"""Unit tests for the platform EnvelopeCodec."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.platform.application.ports.delivery_transport import DeliveryEnvelope
from shell.platform.infrastructure.messaging.transport import EnvelopeCodec


def _envelope() -> DeliveryEnvelope:
    return DeliveryEnvelope(
        kind="event",
        delivery_id="delivery-1",
        delivery_type="TaskExecutionCreatedEvent",
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"task_execution_id": "abc"},
        correlation_id="corr-1",
        causation_id="cause-1",
    )


class TestEnvelopeCodec:
    def test_round_trip_preserves_fields(self) -> None:
        codec = EnvelopeCodec()
        encoded = codec.encode(_envelope())
        decoded = codec.decode(encoded)

        assert decoded.kind == "event"
        assert decoded.delivery_id == "delivery-1"
        assert decoded.delivery_type == "TaskExecutionCreatedEvent"
        assert decoded.occurred_at == datetime(2026, 1, 1, tzinfo=UTC)
        assert decoded.payload == {"task_execution_id": "abc"}
        assert decoded.correlation_id == "corr-1"
        assert decoded.causation_id == "cause-1"

    def test_naive_occurred_at_normalized_to_utc(self) -> None:
        codec = EnvelopeCodec()
        raw = codec.encode(_envelope()).replace(
            b"2026-01-01T00:00:00+00:00", b"2026-01-01T00:00:00"
        )
        decoded = codec.decode(raw)
        assert decoded.occurred_at.tzinfo is not None

    def test_decode_rejects_unknown_kind(self) -> None:
        codec = EnvelopeCodec()
        raw = codec.encode(_envelope()).replace(b'"kind":"event"', b'"kind":"unknown"')
        try:
            codec.decode(raw)
        except ValueError as exc:
            assert "kind" in str(exc)
        else:
            raise AssertionError("expected ValueError for unknown kind")
