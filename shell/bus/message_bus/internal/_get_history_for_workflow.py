from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.envelope.envelope import Envelope

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _get_history_for_workflow(bus: MessageBus, workflow_id: str) -> list[Envelope]:
    rows = bus.driver_.query(
        """
        SELECT * FROM envelope
        WHERE workflow_id = ?
        ORDER BY sequence_id ASC
        """,
        (workflow_id,),
    )
    return [Envelope.from_row(r) for r in rows]
