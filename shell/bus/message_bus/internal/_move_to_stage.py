from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_stage import EnvelopeStage

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _move_to_stage(
    bus: MessageBus,
    envelope_id: int,
    new_stage: EnvelopeStage,
    source: str | None = None,
    reason: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = bus.driver_.query("SELECT stage FROM envelope WHERE id = ?", (envelope_id,))
    if not rows:
        raise ValueError(f"[MessageBus.move_to_stage] envelope_id={envelope_id} not found")
    old_stage = rows[0]["stage"]
    bus.driver_.execute(
        "UPDATE envelope SET stage = ?, updated_at = ? WHERE id = ?",
        (new_stage.value, now, envelope_id),
    )
    bus.driver_.execute(
        """
        INSERT INTO envelope_event (envelope_id, event_type, from_value, to_value, source, payload_json, timestamp)
        VALUES (?, 'STAGE_CHANGED', ?, ?, ?, ?, ?)
        """,
        (envelope_id, old_stage, new_stage.value, source, reason, now),
    )
    bus.driver_.commit()
