from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bus.workflow_state.workflow_state import WorkflowState


def _get_workflow(state: WorkflowState, workflow_id: str) -> dict | None:
    rows = state.driver_.query(
        "SELECT * FROM workflow WHERE workflow_id = ?",
        (workflow_id,),
    )
    return dict(rows[0]) if rows else None


def _list_node_states(state: WorkflowState, workflow_id: str) -> list[dict]:
    return state.driver_.query(
        "SELECT * FROM node_state WHERE workflow_id = ? ORDER BY node_id",
        (workflow_id,),
    )
