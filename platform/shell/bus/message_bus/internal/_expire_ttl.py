from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_stage import EnvelopeStage

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _expire_ttl(bus: MessageBus, workflow_id: str, max_step: int) -> int:
    now = datetime.now(timezone.utc).isoformat()
    rows = bus.driver_.query(
        """
        SELECT id, stage FROM envelope
        WHERE workflow_id = ? AND step >= ? AND stage NOT IN (?, ?, ?)
        """,
        (workflow_id, max_step, EnvelopeStage.DEAD.value, EnvelopeStage.DONE.value, EnvelopeStage.HISTORY.value),
    )
    if not rows:
        return 0
    for row in rows:
        bus.driver_.execute(
            "UPDATE envelope SET stage = ?, updated_at = ? WHERE id = ?",
            (EnvelopeStage.DEAD.value, now, row["id"]),
        )
        bus.driver_.execute(
            """
            INSERT INTO envelope_event (envelope_id, event_type, from_value, to_value, source, timestamp)
            VALUES (?, 'EXPIRED', ?, ?, 'router', ?)
            """,
            (row["id"], row["stage"], EnvelopeStage.DEAD.value, now),
        )
    bus.driver_.commit()
    return len(rows)
