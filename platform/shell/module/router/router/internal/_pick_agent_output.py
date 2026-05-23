from __future__ import annotations


from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.module.router.router.internal._assert_graph_node_role_set import _assert_graph_node_role_set
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _message_id_sort_key(filename: str) -> int:
    parsed = parse_message_filename(filename)
    if parsed is None:
        return -1
    try:
        return int(parsed.message_id)
    except ValueError:
        return -1


def _pick_agent_output(app, agent_nodes) -> tuple[PathType, str] | None:
    all_candidates = []
    for graph_node in agent_nodes:
        agent_output_dir = graph_node.sub_node_properties_.node_dir_ / DOT_NODE / DIR_OUTPUT
        app.app_trace_.record_info('router._pick_agent_output', f'scanning: {agent_output_dir}')
        if not Path.exists(agent_output_dir):
            continue
        role = graph_node.role_
        _assert_graph_node_role_set(role, graph_node.node_name_)
        for f in Path.iterdir(agent_output_dir):
            if Path.is_file(f):
                all_candidates.append((f, role))
    app.app_trace_.record_info(
        'router._pick_agent_output',
        f'candidates={len(all_candidates)}'
    )
    if not all_candidates:
        return None
    all_candidates.sort(key=lambda pair: _message_id_sort_key(pair[0].name))
    picked_file, source_role = all_candidates[0]
    app.app_trace_.record_info(
        'router._pick_agent_output',
        f'picked: {picked_file.name} from role={source_role}'
    )
    return picked_file, source_role
