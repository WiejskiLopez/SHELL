from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_stage import EnvelopeStage
from shell.bus.envelope.envelope_status import EnvelopeStatus
from shell.bus.message_bus.internal._next_sequence_id import _next_sequence_id

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _publish_envelope(
    bus: MessageBus,
    workflow_id: str,
    source_role: str,
    payload: dict,
    parent_envelope_id: int | None = None,
    correlation_id: str | None = None,
    sender_node_id: str | None = None,
    receiver_node_id: str | None = None,
    target_role: str | None = None,
    step: int = 0,
    status: EnvelopeStatus = EnvelopeStatus.REQUESTED,
    stage: EnvelopeStage | None = None,
    artifact_uri: str | None = None,
) -> int:
    if stage is None:
        stage = EnvelopeStage.ACTIVE if receiver_node_id else EnvelopeStage.PENDING
    now = datetime.now(timezone.utc).isoformat()
    sequence_id = _next_sequence_id(bus, workflow_id)
    payload_json = json.dumps(payload, ensure_ascii=False)

    bus.driver_.execute(
        """
        INSERT INTO envelope (
            workflow_id, parent_envelope_id, correlation_id,
            sender_node_id, receiver_node_id, source_role, target_role,
            sequence_id, step, status, stage, payload_json,
            artifact_uri, archive_uri, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
        """,
        (
            workflow_id, parent_envelope_id, correlation_id,
            sender_node_id, receiver_node_id, source_role, target_role,
            sequence_id, step, status.value, stage.value, payload_json,
            artifact_uri, now, now,
        ),
    )
    envelope_id = bus.driver_.last_insert_id()
    bus.driver_.execute(
        """
        INSERT INTO envelope_event (envelope_id, event_type, to_value, source, payload_json, timestamp)
        VALUES (?, 'CREATED', ?, ?, ?, ?)
        """,
        (envelope_id, stage.value, sender_node_id, payload_json, now),
    )
    bus.driver_.commit()
    return envelope_id
