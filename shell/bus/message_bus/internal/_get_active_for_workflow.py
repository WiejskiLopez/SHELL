from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.envelope.envelope import Envelope
from shell.bus.envelope.envelope_stage import EnvelopeStage

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _get_active_for_workflow(bus: MessageBus, workflow_id: str) -> list[Envelope]:
    rows = bus.driver_.query(
        """
        SELECT * FROM envelope
        WHERE workflow_id = ? AND stage = ?
        ORDER BY sequence_id ASC
        """,
        (workflow_id, EnvelopeStage.ACTIVE.value),
    )
    return [Envelope.from_row(r) for r in rows]
