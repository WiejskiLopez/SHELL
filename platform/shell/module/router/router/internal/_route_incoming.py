from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router.parse_message_filename import FROM_PLACEHOLDER
from shell.module.router.router.parse_message_filename import build_message_filename
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._assert_step_within_ttl import _assert_step_within_ttl
from shell.module.router.router.internal._distribute_active import _distribute_active
from shell.module.router.router_stage.internal._match_pending import _match_pending
from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _route_incoming(router: 'Router', node_stage, graph_nodes, picked_file: PathType, source_role: str, app) -> None:
    max_step = app.cli_.cli_properties_.max_step_

    parsed = parse_message_filename(picked_file.name)
    if parsed is not None:
        _assert_step_within_ttl(parsed, max_step)
    if parsed is not None and parsed.from_role == FROM_PLACEHOLDER:
        dest_name = build_message_filename(parsed, from_role=source_role)
    else:
        dest_name = picked_file.name

    app.app_trace_.record_info(
        'router._route_incoming',
        f'routing: {picked_file.name} msg_type={parsed.msg_type if parsed else None} to_role={parsed.to_role if parsed else None}'
    )

    if parsed is not None and parsed.msg_type == 'DONE':
        app.app_trace_.record_info('router._route_incoming', f'DONE received: {picked_file.name}')
        node_stage.save_to_done(picked_file)
        Path.unlink(picked_file)
        return

    if parsed is not None and parsed.to_role == 'router':
        matched_pending = _match_pending(node_stage, parsed)
        if matched_pending is not None:
            app.app_trace_.record_info('router._route_incoming', f'matched pending: {matched_pending.name}')
            node_stage.move_pending_to_history(matched_pending.name)
        app.app_trace_.record_info('router._route_incoming', f'saving to history: {picked_file.name}')
        node_stage.save_to_history(picked_file)
        Path.unlink(picked_file)
        return

    app.app_trace_.record_info('router._route_incoming', f'saving to active: {dest_name}')
    if picked_file.parent.name != 'active':
        node_stage.save_to_active(picked_file, dest_name=dest_name)
        Path.unlink(picked_file)
    _distribute_active(router, node_stage, graph_nodes, app)
