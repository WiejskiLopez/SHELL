from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.workflow_state.workflow_state import WorkflowState


def _open_workflow(
    state: WorkflowState,
    workflow_id: str,
    root_task_id: str | None = None,
    parent_workflow_id: str | None = None,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state.driver_.execute(
        """
        INSERT INTO workflow (workflow_id, parent_workflow_id, root_task_id, status, started_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(workflow_id) DO UPDATE SET
            parent_workflow_id = excluded.parent_workflow_id,
            root_task_id       = excluded.root_task_id,
            status             = excluded.status,
            started_at         = excluded.started_at
        """,
        (workflow_id, parent_workflow_id, root_task_id, "ACTIVE", now),
    )
    state.driver_.commit()
