from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._expire_pending_ttl import _expire_pending_ttl
from shell.module.router.router.internal._flush_done import _flush_done
from shell.module.router.router.internal._pick_agent_output import _pick_agent_output
from shell.module.router.router.internal._assert_active_file_parsed import _assert_active_file_parsed
from shell.module.router.router.internal._pick_active_file import _pick_active_file
from shell.module.router.router.internal._pick_parent_input import _pick_parent_input
from shell.module.router.router.internal._rename_parent_input_as_task import _rename_parent_input_as_task
from shell.module.router.router.internal._route_incoming import _route_incoming
from shell.module.router.router.internal._seed_tasker_input_to_first_agent import _seed_tasker_input_to_first_agent

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _run_router(router: 'Router') -> None:
    app = router._app
    max_step = app.cli_.cli_properties_.max_step_
    node_stage = router.router_stage_.node_stage_

    graph_nodes = router.router_base_.graph_nodes_
    non_router_nodes = [pn for pn in graph_nodes if pn.mode_ != 'router']

    _expire_pending_ttl(app, node_stage, max_step)

    agent_result = _pick_agent_output(app, non_router_nodes)
    active_file = _pick_active_file(app, node_stage)
    parent_input_file = _pick_parent_input(app)
    app.app_trace_.record_info('router._run_router', f'agent_result={agent_result[0].name if agent_result else None}')
    app.app_trace_.record_info('router._run_router', f'active_file={active_file.name if active_file else None}')
    app.app_trace_.record_info('router._run_router', f'parent_input_file={parent_input_file.name if parent_input_file else None}')

    if agent_result is not None:
        picked_file, source_role = agent_result
    elif active_file is not None:
        _parsed = parse_message_filename(active_file.name)
        _assert_active_file_parsed(_parsed, active_file)
        picked_file, source_role = active_file, _parsed.from_role
        app.app_trace_.record_info(
            'router._run_router',
            f'routing from active: {active_file.name} from_role={source_role}'
        )
    elif parent_input_file is not None:
        if not non_router_nodes:
            app.app_trace_.record_info('router._run_router', 'parent input found but no target nodes — skipping')
            return
        first_role = non_router_nodes[0].role_
        role = app.cli_.cli_properties_.role_
        renamed = _rename_parent_input_as_task(parent_input_file, app, first_role, role)
        picked_file, source_role = renamed, role
        app.app_trace_.record_info(
            'router._run_router',
            f'routing parent input as TASK: {renamed.name} to_role={first_role}'
        )
    else:
        if not node_stage.get_active_files():
            _flush_done(app, node_stage)
        return

    _route_incoming(router, node_stage, graph_nodes, picked_file, source_role, app)

