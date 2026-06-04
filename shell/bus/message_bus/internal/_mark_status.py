from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _mark_status(
    bus: MessageBus,
    envelope_id: int,
    new_status: EnvelopeStatus,
    source: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    rows = bus.driver_.query("SELECT status FROM envelope WHERE id = ?", (envelope_id,))
    if not rows:
        raise ValueError(f"[MessageBus.mark_status] envelope_id={envelope_id} not found")
    old_status = rows[0]["status"]
    bus.driver_.execute(
        "UPDATE envelope SET status = ?, updated_at = ? WHERE id = ?",
        (new_status.value, now, envelope_id),
    )
    bus.driver_.execute(
        """
        INSERT INTO envelope_event (envelope_id, event_type, from_value, to_value, source, timestamp)
        VALUES (?, 'STATUS_CHANGED', ?, ?, ?, ?)
        """,
        (envelope_id, old_status, new_status.value, source, now),
    )
    bus.driver_.commit()
