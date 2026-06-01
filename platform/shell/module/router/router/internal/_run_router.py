"""_run_router.py
Router run: bus-based routing pass.

Moves PENDING envelopes (no receiver_node_id yet) to ACTIVE by resolving
target_role -> receiver_node_id via graph role map. Envelopes without
target_role are routed to the next graph node.

Also expires envelopes whose step >= max_step (move to DEAD).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_stage import EnvelopeStage

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _run_router(router: 'Router') -> None:
    app = router._app
    bus = app.bus_
    workflow_id = _resolve_workflow_id(app)
    max_step = app.cli_.cli_properties_.max_step_

    expired_count = bus.expire_ttl(workflow_id, max_step) if max_step else 0
    app.app_trace_.record_info('router._run_router', f'expired_count={expired_count}')

    pending = [
        e for e in bus.get_history_for_workflow(workflow_id)
        if e.stage_ == EnvelopeStage.PENDING
    ]
    app.app_trace_.record_info('router._run_router', f'pending_count={len(pending)}')

    role_to_node = router.router_base_.role_to_node_map_
    graph_nodes = router.router_base_.graph_nodes_
    non_router_nodes = [n for n in graph_nodes if n.mode_ != 'router']

    routed = 0
    for envelope in pending:
        target_role = envelope.target_role_
        target_node = role_to_node.get(target_role) if target_role else None
        if target_node is None and non_router_nodes:
            target_node = non_router_nodes[0]
        if target_node is None:
            app.app_trace_.record_info(
                'router._run_router',
                f'envelope id={envelope.id_} target_role={target_role!r} unresolved — skip',
            )
            continue
        bus.driver_.execute(
            "UPDATE envelope SET receiver_node_id = ?, stage = ? WHERE id = ?",
            (target_node.node_name_, EnvelopeStage.ACTIVE.value, envelope.id_),
        )
        bus.driver_.execute(
            """
            INSERT INTO envelope_event (envelope_id, event_type, from_value, to_value, source)
            VALUES (?, 'STAGE_CHANGED', ?, ?, 'router')
            """,
            (envelope.id_, EnvelopeStage.PENDING.value, EnvelopeStage.ACTIVE.value),
        )
        bus.driver_.commit()
        routed += 1
        app.app_trace_.record_info(
            'router._run_router',
            f'routed envelope id={envelope.id_} target_role={target_role} -> node={target_node.node_name_}',
        )

    app.app_trace_.record_info('router._run_router', f'routed={routed}')


def _resolve_workflow_id(app) -> str:
    task_name = app.cli_.cli_properties_.task_name_
    if task_name:
        return task_name
    return app.app_node_.node_.node_dir_.name
