"""EnvelopeCodec — JSON (de)serialization of DeliveryEnvelope for the broker wire format."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from shell.platform.application.ports.transport.delivery_transport import (
    DeliveryEnvelope,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class EnvelopeCodec:
    """Encodes a DeliveryEnvelope to JSON bytes and back.

    The wire format is a flat JSON envelope. The contract type key is specific
    to the delivery kind, for example ``event_type`` for events.
    """

    def encode(self, envelope: DeliveryEnvelope) -> bytes:
        raw_occurred_at = envelope.occurred_at
        if hasattr(raw_occurred_at, "isoformat"):
            occurred_at = raw_occurred_at.isoformat()
        else:
            occurred_at = str(raw_occurred_at)
        contract_type_key = f"{envelope.kind}_type"
        document: dict[str, object] = {
            "kind": envelope.kind,
            "outbox_id": envelope.outbox_id,
            contract_type_key: envelope.contract_type,
            "occurred_at": occurred_at,
            "schema_version": envelope.schema_version,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
        }
        if envelope.kind == "event":
            document.update(
                {
                    "event_id": envelope.event_id,
                    "source_service": envelope.source_service,
                    "aggregate_id": envelope.aggregate_id,
                    "aggregate_name": envelope.aggregate_name,
                }
            )
        return json.dumps(document, separators=(",", ":")).encode("utf-8")

    def decode(self, raw: bytes) -> DeliveryEnvelope:
        document: Mapping[str, object] = json.loads(raw.decode("utf-8"))
        kind = document["kind"]
        if kind not in ("event", "message", "command"):
            raise ValueError(f"Unknown delivery kind: {kind}")
        contract_type_key = f"{kind}_type"
        occurred_at = self._parse_occurred_at(str(document["occurred_at"]))
        return DeliveryEnvelope(
            kind=kind,
            outbox_id=str(document["outbox_id"]),
            contract_type=str(document[contract_type_key]),
            occurred_at=occurred_at,
            payload=dict(cast("Mapping[str, object]", document["payload"]))
            if document.get("payload")
            else {},
            correlation_id=str(document.get("correlation_id", "")),
            causation_id=str(document.get("causation_id", "")),
            event_id=str(document["event_id"]) if document.get("event_id") else None,
            source_service=(
                str(document["source_service"]) if document.get("source_service") else None
            ),
            aggregate_id=(str(document["aggregate_id"]) if document.get("aggregate_id") else None),
            aggregate_name=(
                str(document["aggregate_name"]) if document.get("aggregate_name") else None
            ),
            schema_version=cast("int", document.get("schema_version", 1)),
        )

    @staticmethod
    def _parse_occurred_at(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
