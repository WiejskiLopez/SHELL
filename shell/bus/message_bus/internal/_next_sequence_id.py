from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.message_bus.message_bus import MessageBus


def _next_sequence_id(bus: MessageBus, workflow_id: str) -> int:
    rows = bus.driver_.query(
        "SELECT COALESCE(MAX(sequence_id), 0) + 1 AS next FROM envelope WHERE workflow_id = ?",
        (workflow_id,),
    )
    return int(rows[0]["next"])
