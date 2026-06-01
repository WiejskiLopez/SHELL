from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.envelope.envelope import Envelope

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _get_envelope(bus: MessageBus, envelope_id: int) -> Envelope | None:
    rows = bus.driver_.query("SELECT * FROM envelope WHERE id = ?", (envelope_id,))
    if not rows:
        return None
    return Envelope.from_row(rows[0])
