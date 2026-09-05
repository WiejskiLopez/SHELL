"""EventEnvelopeCodec — JSON (de)serialization of the integration-event envelope."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from shell.platform.application.ports.transport.event_transport import (
    EventDeliveryEnvelope,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class EnvelopeCodec:
    """Encodes an integration-event delivery envelope to JSON bytes and back.

    The wire carries ``contract_type`` (stable contract name) and ``occurred_at``;
    event metadata is stored in dedicated fields, not the payload. The channel is
    implied by the envelope type, so no ``kind``/``outbox_id`` is on the wire.
    """

    def encode(self, envelope: EventDeliveryEnvelope) -> bytes:
        raw_occurred_at = envelope.occurred_at
        occurred_at = (
            raw_occurred_at.isoformat()
            if hasattr(raw_occurred_at, "isoformat")
            else str(raw_occurred_at)
        )
        document: dict[str, object] = {
            "contract_type": envelope.contract_type,
            "occurred_at": occurred_at,
            "schema_version": envelope.schema_version,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
            "event_id": envelope.event_id,
            "source_service": envelope.source_service,
            "destination_service": envelope.destination_service,
            "aggregate_id": envelope.aggregate_id,
        }
        return json.dumps(document, separators=(",", ":")).encode("utf-8")

    def decode(self, raw: bytes) -> EventDeliveryEnvelope:
        document: Mapping[str, object] = json.loads(raw.decode("utf-8"))
        return EventDeliveryEnvelope(
            contract_type=str(document["contract_type"]),
            occurred_at=self._parse_occurred_at(str(document["occurred_at"])),
            payload=dict(cast("Mapping[str, object]", document["payload"]))
            if document.get("payload")
            else {},
            correlation_id=str(document.get("correlation_id", "")),
            causation_id=str(document.get("causation_id", "")),
            schema_version=cast("int", document.get("schema_version", 1)),
            event_id=str(document["event_id"]) if document.get("event_id") else "",
            source_service=(
                str(document["source_service"]) if document.get("source_service") else ""
            ),
            destination_service=(
                str(document["destination_service"])
                if document.get("destination_service")
                else ""
            ),
            aggregate_id=(
                str(document["aggregate_id"]) if document.get("aggregate_id") else ""
            ),
        )

    @staticmethod
    def _parse_occurred_at(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)