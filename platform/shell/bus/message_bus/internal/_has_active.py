from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_stage import EnvelopeStage

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _has_active(bus: MessageBus, workflow_id: str) -> bool:
    rows = bus.driver_.query(
        """
        SELECT 1 FROM envelope
        WHERE workflow_id = ? AND stage IN (?, ?)
        LIMIT 1
        """,
        (workflow_id, EnvelopeStage.ACTIVE.value, EnvelopeStage.PENDING.value),
    )
    return bool(rows)
