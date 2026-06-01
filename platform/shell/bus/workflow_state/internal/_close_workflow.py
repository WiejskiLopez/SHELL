from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.workflow_state.workflow_state import WorkflowState


def _close_workflow(state: WorkflowState, workflow_id: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state.driver_.execute(
        "UPDATE workflow SET status = ?, ended_at = ? WHERE workflow_id = ?",
        (status, now, workflow_id),
    )
    state.driver_.commit()
