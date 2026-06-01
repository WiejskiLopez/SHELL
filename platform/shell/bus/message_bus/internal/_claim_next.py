from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope import Envelope
from shell.bus.envelope.envelope_stage import EnvelopeStage
from shell.bus.envelope.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _claim_next(
    bus: MessageBus,
    workflow_id: str,
    receiver_node_id: str,
) -> Envelope | None:
    bus.driver_.execute("BEGIN IMMEDIATE")
    try:
        rows = bus.driver_.query(
            """
            SELECT id FROM envelope
            WHERE workflow_id = ?
              AND receiver_node_id = ?
              AND stage = ?
              AND status IN (?, ?)
            ORDER BY sequence_id ASC
            LIMIT 1
            """,
            (
                workflow_id,
                receiver_node_id,
                EnvelopeStage.ACTIVE.value,
                EnvelopeStatus.REQUESTED.value,
                EnvelopeStatus.WAITING.value,
            ),
        )
        if not rows:
            bus.driver_.commit()
            return None
        envelope_id = rows[0]["id"]
        now = datetime.now(timezone.utc).isoformat()
        bus.driver_.execute(
            "UPDATE envelope SET status = ?, updated_at = ? WHERE id = ?",
            (EnvelopeStatus.DISPATCHED.value, now, envelope_id),
        )
        bus.driver_.execute(
            """
            INSERT INTO envelope_event (envelope_id, event_type, from_value, to_value, source, timestamp)
            VALUES (?, 'STATUS_CHANGED', ?, ?, ?, ?)
            """,
            (envelope_id, EnvelopeStatus.REQUESTED.value, EnvelopeStatus.DISPATCHED.value, "router", now),
        )
        full_rows = bus.driver_.query(
            "SELECT * FROM envelope WHERE id = ?",
            (envelope_id,),
        )
        bus.driver_.commit()
        return Envelope.from_row(full_rows[0])
    except Exception:
        bus.driver_.execute("ROLLBACK")
        raise
