from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.module.router.router.parse_message_filename import increment_step
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.status.status import Status
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _distribute_active(router: 'Router', node_stage, graph_nodes, app) -> None:
    active_files = node_stage.get_active_files()
    app.app_trace_.record_info('router._distribute_active', f'distributing {len(active_files)} active file(s)')
    for active_file in active_files:
        active_parsed = parse_message_filename(active_file.name)
        target_role = active_parsed.to_role if active_parsed is not None else None
        target_node = (
            router.router_base_.role_to_node_map_.get(target_role) if target_role
            else router.get_next_graph_node()
        )
        if target_node is None:
            continue
        distributed_name = increment_step(active_parsed) if active_parsed is not None else active_file.name
        dest_dir = app.app_node_.node_.node_dir_.parent / target_node.node_name_ / DOT_NODE / DIR_INPUT
        Path.mkdir(dest_dir)
        Path.copy_to(active_file, dest_dir / distributed_name)
        app.app_trace_.record_info(
            'router._distribute_active',
            f'copied {active_file.name} -> node={target_node.node_name_} dir={dest_dir}'
        )
        target_graph_node = next(
            (pn for pn in graph_nodes if pn.role_ == target_role),
            None,
        ) if target_role else next(
            (pn for pn in graph_nodes if pn.mode_ == 'agent'),
            None,
        )
        if target_graph_node is not None:
            target_graph_node.node_status_.set_status(Status.READY)
            _persist_node_status(target_graph_node, app)
            app.app_trace_.record_info(
                'router._run_router._run_router',
                f'node {target_graph_node.node_name_} status=READY'
            )
        if active_parsed is not None and active_parsed.msg_type == 'QUESTION':
            node_stage.move_to_pending(active_file.name)
        else:
            node_stage.move_to_history(active_file.name)
