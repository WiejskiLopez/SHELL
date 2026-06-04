from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _get_envelope_events(bus: MessageBus, envelope_id: int) -> list[dict]:
    return bus.driver_.query(
        """
        SELECT id, envelope_id, event_type, from_value, to_value, source, payload_json, timestamp
        FROM envelope_event
        WHERE envelope_id = ?
        ORDER BY id ASC
        """,
        (envelope_id,),
    )
