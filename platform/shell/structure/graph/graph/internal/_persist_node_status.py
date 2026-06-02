from __future__ import annotations


def _persist_node_status(sub_node, app, workflow_id: str) -> None:
    app.workflow_state_.set_node_status(
        workflow_id=workflow_id,
        node_id=sub_node.node_name_,
        role=getattr(sub_node, 'mode_', None),
        current_status=sub_node.status_.name,
    )
    app.app_trace_.record_info(
        'graph._persist_node_status._persist_node_status',
        f'persisted status={sub_node.status_.name} for node {sub_node.node_name_} (workflow={workflow_id})'
    )
