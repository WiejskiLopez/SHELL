from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.workflow_state.workflow_state import WorkflowState


def _set_node_status(
    state: WorkflowState,
    workflow_id: str,
    node_id: str,
    role: str | None,
    current_status: str,
    last_envelope_id: int | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state.driver_.execute(
        """
        INSERT INTO node_state (workflow_id, node_id, role, current_status, last_envelope_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(workflow_id, node_id) DO UPDATE SET
            role             = excluded.role,
            current_status   = excluded.current_status,
            last_envelope_id = excluded.last_envelope_id,
            updated_at       = excluded.updated_at
        """,
        (workflow_id, node_id, role, current_status, last_envelope_id, now),
    )
    state.driver_.commit()
