"""EnvelopeCodec — JSON (de)serialization of DeliveryEnvelope for the broker wire format."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from shell.platform.application.ports.delivery_transport import (
    DeliveryEnvelope,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class EnvelopeCodec:
    """Encodes a DeliveryEnvelope to JSON bytes and back.

    The wire format is a flat JSON object:
    ``{kind, delivery_id, delivery_type, occurred_at, payload, correlation_id, causation_id}``.
    """

    def encode(self, envelope: DeliveryEnvelope) -> bytes:
        raw_occurred_at = envelope.occurred_at
        if hasattr(raw_occurred_at, "isoformat"):
            occurred_at = raw_occurred_at.isoformat()
        else:
            occurred_at = str(raw_occurred_at)
        document: dict[str, object] = {
            "kind": envelope.kind,
            "delivery_id": envelope.delivery_id,
            "delivery_type": envelope.delivery_type,
            "occurred_at": occurred_at,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
        }
        return json.dumps(document, separators=(",", ":")).encode("utf-8")

    def decode(self, raw: bytes) -> DeliveryEnvelope:
        document: Mapping[str, object] = json.loads(raw.decode("utf-8"))
        kind = document["kind"]
        if kind not in ("event", "message", "command"):
            raise ValueError(f"Unknown delivery kind: {kind}")
        occurred_at = self._parse_occurred_at(str(document["occurred_at"]))
        return DeliveryEnvelope(
            kind=kind,
            delivery_id=str(document["delivery_id"]),
            delivery_type=str(document["delivery_type"]),
            occurred_at=occurred_at,
            payload=dict(cast("Mapping[str, object]", document["payload"]))
            if document.get("payload")
            else {},
            correlation_id=str(document.get("correlation_id", "")),
            causation_id=str(document.get("causation_id", "")),
        )

    @staticmethod
    def _parse_occurred_at(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
