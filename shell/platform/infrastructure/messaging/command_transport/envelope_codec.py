"""CommandEnvelopeCodec — JSON (de)serialization of the command envelope."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from shell.platform.application.ports.transport.command_transport import (
    CommandDeliveryEnvelope,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class EnvelopeCodec:
    """Encodes a command delivery envelope to JSON bytes and back.

    The wire carries ``contract_type`` (the stable contract name),
    ``source_service`` and ``destination_service``; transport metadata is never
    part of the command payload. The channel is implied by the envelope type, so
    no ``kind``/``outbox_id`` is on the wire.
    """

    def encode(self, envelope: CommandDeliveryEnvelope) -> bytes:
        raw_issued_at = envelope.issued_at
        issued_at = (
            raw_issued_at.isoformat()
            if hasattr(raw_issued_at, "isoformat")
            else str(raw_issued_at)
        )
        document: dict[str, object] = {
            "command_id": envelope.command_id,
            "contract_type": envelope.contract_type,
            "source_service": envelope.source_service,
            "destination_service": envelope.destination_service,
            "issued_at": issued_at,
            "schema_version": envelope.schema_version,
            "payload": envelope.payload,
            "correlation_id": envelope.correlation_id,
            "causation_id": envelope.causation_id,
        }
        return json.dumps(document, separators=(",", ":")).encode("utf-8")

    def decode(self, raw: bytes) -> CommandDeliveryEnvelope:
        document: Mapping[str, object] = json.loads(raw.decode("utf-8"))
        return CommandDeliveryEnvelope(
            command_id=str(document["command_id"]),
            contract_type=str(document["contract_type"]),
            source_service=str(document.get("source_service", "")),
            destination_service=str(document.get("destination_service", "")),
            issued_at=self._parse_issued_at(str(document["issued_at"])),
            payload=dict(cast("Mapping[str, object]", document["payload"]))
            if document.get("payload")
            else {},
            correlation_id=str(document.get("correlation_id", "")),
            causation_id=str(document.get("causation_id", "")),
            schema_version=cast("int", document.get("schema_version", 1)),
        )

    @staticmethod
    def _parse_issued_at(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)